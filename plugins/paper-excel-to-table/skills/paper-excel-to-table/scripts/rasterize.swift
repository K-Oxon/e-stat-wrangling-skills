#!/usr/bin/env swift
// rasterize.swift — Render PDF pages to high-resolution PNGs using PDFKit + Core Graphics.
//
// Usage:
//   swift rasterize.swift <pdf_path> <out_dir> \
//       [--dpi 300] [--box media|crop] [--colorspace sRGB|Gray] \
//       [--alpha] [--no-annots] [--pages 1-|1,3,5|2-4,7]
//   swift rasterize.swift --selftest
//
// Default --dpi is 300: A4 portrait renders at 2481x3508 px (~8.7 MP), above
// Claude Opus 4.7's ~2576 px / ~3.75 MP vision input. The API downscales on
// upload; we intentionally keep the raw PNG at max detail so the crop pipeline
// (docs/dev/plugins/paper-excel-to-table.md §3) can cut logical blocks at
// native resolution when per-page accuracy is insufficient.
//
// stdout: one JSON object (Backend contract, docs/dev/plugins/paper-excel-to-table.md §4.3).
// stderr: human-readable logs.

#if !os(macOS)
#error("rasterize.swift requires macOS (PDFKit + AppKit).")
#endif

import AppKit
import CoreGraphics
import Foundation
import ImageIO
import PDFKit
import UniformTypeIdentifiers

// MARK: - Errors

enum RasterizeError: Error, CustomStringConvertible {
    case usage(String)
    case pdfOpenFailed(String)
    case emptyPDF
    case pageOutOfRange(Int, Int)
    case pagesParseFailed(String)
    case contextFailed(Int)
    case imageFailed(Int)
    case pngWriteFailed(String)
    case outDirCreateFailed(String, Error)

    var description: String {
        switch self {
        case .usage(let msg): return "usage: \(msg)"
        case .pdfOpenFailed(let path): return "failed to open PDF: \(path)"
        case .emptyPDF: return "PDF has zero pages"
        case .pageOutOfRange(let idx, let total):
            return "page index \(idx) out of range 1...\(total)"
        case .pagesParseFailed(let raw): return "could not parse --pages '\(raw)'"
        case .contextFailed(let idx): return "CGContext creation failed on page \(idx)"
        case .imageFailed(let idx): return "CGContext.makeImage failed on page \(idx)"
        case .pngWriteFailed(let path): return "PNG write failed: \(path)"
        case .outDirCreateFailed(let path, let err):
            return "could not create out_dir '\(path)': \(err)"
        }
    }

    var exitCode: Int32 {
        if case .usage = self { return 2 }
        return 1
    }
}

// MARK: - Options

struct Options {
    var pdfPath: String
    var outDir: String
    var dpi: Int = 300
    var box: PDFDisplayBox = .mediaBox
    var boxName: String = "media"
    var useGray: Bool = false
    var colorspaceName: String = "sRGB"
    var alpha: Bool = false
    var annots: Bool = true
    var pagesSpec: String? = nil
}

// MARK: - Argument parsing

func parseArgs(_ argv: [String]) throws -> Options {
    // Drop argv[0]; when run as `swift script.swift a b`, CommandLine.arguments = ["script.swift", "a", "b"].
    var args = Array(argv.dropFirst())

    if args.first == "--selftest" {
        selftest()
    }

    var positional: [String] = []
    var opt = Options(pdfPath: "", outDir: "")

    var i = 0
    while i < args.count {
        let a = args[i]
        switch a {
        case "--dpi":
            guard i + 1 < args.count, let v = Int(args[i+1]), v > 0 else {
                throw RasterizeError.usage("--dpi requires positive integer")
            }
            opt.dpi = v
            i += 2
        case "--box":
            guard i + 1 < args.count else { throw RasterizeError.usage("--box requires value") }
            let v = args[i+1]
            switch v {
            case "media": opt.box = .mediaBox;  opt.boxName = "media"
            case "crop":  opt.box = .cropBox;   opt.boxName = "crop"
            default: throw RasterizeError.usage("--box must be media|crop")
            }
            i += 2
        case "--colorspace":
            guard i + 1 < args.count else { throw RasterizeError.usage("--colorspace requires value") }
            let v = args[i+1]
            switch v {
            case "sRGB": opt.useGray = false; opt.colorspaceName = "sRGB"
            case "Gray": opt.useGray = true;  opt.colorspaceName = "Gray"
            default: throw RasterizeError.usage("--colorspace must be sRGB|Gray")
            }
            i += 2
        case "--alpha":
            opt.alpha = true
            i += 1
        case "--no-annots":
            opt.annots = false
            i += 1
        case "--pages":
            guard i + 1 < args.count else { throw RasterizeError.usage("--pages requires value") }
            opt.pagesSpec = args[i+1]
            i += 2
        case "-h", "--help":
            printUsage()
            exit(0)
        default:
            if a.hasPrefix("--") {
                throw RasterizeError.usage("unknown option '\(a)'")
            }
            positional.append(a)
            i += 1
        }
    }

    guard positional.count == 2 else {
        throw RasterizeError.usage("expected <pdf_path> <out_dir>, got \(positional.count) positional args")
    }
    opt.pdfPath = positional[0]
    opt.outDir = positional[1]
    return opt
}

func printUsage() {
    let usage = """
    Usage: swift rasterize.swift <pdf_path> <out_dir> [options]

    Options:
      --dpi N              Rendering DPI (default 300; A4 ≈ 2481x3508 px / 8.7 MP)
      --box media|crop     Page box to render (default media)
      --colorspace sRGB|Gray  Output colorspace (default sRGB)
      --alpha              Keep alpha channel (transparent background)
      --no-annots          Suppress PDF annotations
      --pages SPEC         e.g. "1-" | "1-5" | "1,3,5" | "2-4,7"
      --selftest           Run a minimal self-check and exit
      -h, --help           Show this message
    """
    FileHandle.standardError.write(Data((usage + "\n").utf8))
}

// MARK: - Pages parser

func parsePages(_ spec: String, pageCount: Int) throws -> [Int] {
    var result = Set<Int>()
    let parts = spec.split(separator: ",", omittingEmptySubsequences: true)
    for rawPart in parts {
        let part = rawPart.trimmingCharacters(in: .whitespaces)
        if part.isEmpty { continue }
        if part.contains("-") {
            let rangeParts = part.split(separator: "-", maxSplits: 1, omittingEmptySubsequences: false)
            guard rangeParts.count == 2 else {
                throw RasterizeError.pagesParseFailed(spec)
            }
            let loStr = rangeParts[0].trimmingCharacters(in: .whitespaces)
            let hiStr = rangeParts[1].trimmingCharacters(in: .whitespaces)
            let lo = loStr.isEmpty ? 1 : (Int(loStr) ?? -1)
            let hi = hiStr.isEmpty ? pageCount : (Int(hiStr) ?? -1)
            if lo < 1 || hi < 1 || lo > hi {
                throw RasterizeError.pagesParseFailed(spec)
            }
            for p in lo...hi {
                if p < 1 || p > pageCount {
                    throw RasterizeError.pageOutOfRange(p, pageCount)
                }
                result.insert(p)
            }
        } else {
            guard let p = Int(part) else {
                throw RasterizeError.pagesParseFailed(spec)
            }
            if p < 1 || p > pageCount {
                throw RasterizeError.pageOutOfRange(p, pageCount)
            }
            result.insert(p)
        }
    }
    if result.isEmpty {
        throw RasterizeError.pagesParseFailed(spec)
    }
    return result.sorted()
}

// MARK: - Rendering

struct PageResult {
    let index: Int
    let path: String
    let widthPt: Double
    let heightPt: Double
    let widthPx: Int
    let heightPx: Int
    let megapixels: Double
}

func renderPage(
    _ page: PDFPage,
    index: Int,
    options: Options,
    outURL: URL
) throws -> PageResult {
    let bounds = page.bounds(for: options.box)
    let scale = CGFloat(options.dpi) / 72.0
    let widthPx = max(1, Int((bounds.width * scale).rounded()))
    let heightPx = max(1, Int((bounds.height * scale).rounded()))

    let colorSpace: CGColorSpace = options.useGray
        ? CGColorSpaceCreateDeviceGray()
        : (CGColorSpace(name: CGColorSpace.sRGB) ?? CGColorSpaceCreateDeviceRGB())

    // Pick a bitmap format that CGContext supports:
    //   sRGB + alpha  -> premultipliedLast (RGBA)
    //   sRGB no-alpha -> noneSkipLast      (RGBX, background opaque)
    //   Gray + alpha  -> premultipliedLast (GA)
    //   Gray no-alpha -> noneSkipLast      (effectively opaque gray)
    let bitmapInfo: UInt32 = options.alpha
        ? CGImageAlphaInfo.premultipliedLast.rawValue
        : CGImageAlphaInfo.noneSkipLast.rawValue

    guard let ctx = CGContext(
        data: nil,
        width: widthPx,
        height: heightPx,
        bitsPerComponent: 8,
        bytesPerRow: 0,
        space: colorSpace,
        bitmapInfo: bitmapInfo
    ) else {
        throw RasterizeError.contextFailed(index)
    }

    // Opaque white background when alpha is off; skip the fill when caller asked for alpha.
    if !options.alpha {
        ctx.setFillColor(CGColor(gray: 1.0, alpha: 1.0))
        ctx.fill(CGRect(x: 0, y: 0, width: widthPx, height: heightPx))
    }

    // PDFPage.draw(with:to:) expects a context where (0,0) is the page's bottom-left.
    // CGContext already uses bottom-left; scaleBy handles pt->px and translate handles
    // crop boxes whose origin differs from (0,0).
    ctx.saveGState()
    ctx.scaleBy(x: scale, y: scale)
    ctx.translateBy(x: -bounds.origin.x, y: -bounds.origin.y)

    if !options.annots {
        for a in page.annotations { a.shouldDisplay = false }
    }

    let nsCtx = NSGraphicsContext(cgContext: ctx, flipped: false)
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = nsCtx
    page.draw(with: options.box, to: ctx)
    NSGraphicsContext.restoreGraphicsState()

    ctx.restoreGState()

    guard let image = ctx.makeImage() else {
        throw RasterizeError.imageFailed(index)
    }

    try writePNG(image, to: outURL, dpi: Double(options.dpi))

    let mp = Double(widthPx) * Double(heightPx) / 1_000_000.0
    return PageResult(
        index: index,
        path: outURL.path,
        widthPt: Double(bounds.width),
        heightPt: Double(bounds.height),
        widthPx: widthPx,
        heightPx: heightPx,
        megapixels: mp
    )
}

func writePNG(_ image: CGImage, to url: URL, dpi: Double) throws {
    guard let dest = CGImageDestinationCreateWithURL(
        url as CFURL,
        UTType.png.identifier as CFString,
        1,
        nil
    ) else {
        throw RasterizeError.pngWriteFailed(url.path)
    }
    let dpiNum = NSNumber(value: dpi)
    let props: [CFString: Any] = [
        kCGImagePropertyDPIWidth: dpiNum,
        kCGImagePropertyDPIHeight: dpiNum,
    ]
    CGImageDestinationAddImage(dest, image, props as CFDictionary)
    if !CGImageDestinationFinalize(dest) {
        throw RasterizeError.pngWriteFailed(url.path)
    }
}

// MARK: - Self-test

func selftest() -> Never {
    // Exercise the tricky pieces: CGColorSpace, CGContext (both alpha modes),
    // and CGImageDestination for PNG. Does not require a real PDF.
    guard let rgb = CGColorSpace(name: CGColorSpace.sRGB) else {
        FileHandle.standardError.write(Data("rasterize.swift: selftest FAILED (sRGB colorspace)\n".utf8))
        exit(1)
    }
    let gray = CGColorSpaceCreateDeviceGray()

    func makeCtx(_ cs: CGColorSpace, alpha: Bool) -> Bool {
        let bi: UInt32 = alpha
            ? CGImageAlphaInfo.premultipliedLast.rawValue
            : CGImageAlphaInfo.noneSkipLast.rawValue
        return CGContext(
            data: nil, width: 4, height: 4,
            bitsPerComponent: 8, bytesPerRow: 0,
            space: cs, bitmapInfo: bi
        ) != nil
    }

    let checks: [(String, Bool)] = [
        ("sRGB opaque", makeCtx(rgb, alpha: false)),
        ("sRGB alpha",  makeCtx(rgb, alpha: true)),
        ("Gray opaque", makeCtx(gray, alpha: false)),
        ("Gray alpha",  makeCtx(gray, alpha: true)),
    ]
    for (name, ok) in checks where !ok {
        FileHandle.standardError.write(Data("rasterize.swift: selftest FAILED (\(name))\n".utf8))
        exit(1)
    }

    // PNG round-trip in a temporary file.
    let tmpURL = URL(fileURLWithPath: NSTemporaryDirectory())
        .appendingPathComponent("rasterize-selftest-\(ProcessInfo.processInfo.processIdentifier).png")
    do {
        let ctx = CGContext(
            data: nil, width: 4, height: 4,
            bitsPerComponent: 8, bytesPerRow: 0,
            space: rgb, bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue
        )!
        ctx.setFillColor(CGColor(gray: 1.0, alpha: 1.0))
        ctx.fill(CGRect(x: 0, y: 0, width: 4, height: 4))
        let image = ctx.makeImage()!
        try writePNG(image, to: tmpURL, dpi: 72.0)
        try FileManager.default.removeItem(at: tmpURL)
    } catch {
        FileHandle.standardError.write(Data("rasterize.swift: selftest FAILED (PNG encode): \(error)\n".utf8))
        exit(1)
    }

    FileHandle.standardError.write(Data("rasterize.swift: selftest OK\n".utf8))
    exit(0)
}

// MARK: - Main

func main() {
    do {
        let opt = try parseArgs(CommandLine.arguments)

        // Resolve PDF path.
        let pdfURL = URL(fileURLWithPath: opt.pdfPath).standardizedFileURL
        guard let document = PDFDocument(url: pdfURL) else {
            throw RasterizeError.pdfOpenFailed(pdfURL.path)
        }
        let pageCount = document.pageCount
        guard pageCount > 0 else { throw RasterizeError.emptyPDF }

        // Create out_dir.
        let outURL = URL(fileURLWithPath: opt.outDir).standardizedFileURL
        do {
            try FileManager.default.createDirectory(
                at: outURL, withIntermediateDirectories: true, attributes: nil)
        } catch {
            throw RasterizeError.outDirCreateFailed(outURL.path, error)
        }

        // Determine target pages.
        let targets: [Int]
        if let spec = opt.pagesSpec {
            targets = try parsePages(spec, pageCount: pageCount)
        } else {
            targets = Array(1...pageCount)
        }

        FileHandle.standardError.write(Data(
            "rasterize.swift: pdf=\(pdfURL.lastPathComponent) pages=\(targets.count)/\(pageCount) dpi=\(opt.dpi) box=\(opt.boxName) colorspace=\(opt.colorspaceName) alpha=\(opt.alpha) annots=\(opt.annots)\n".utf8))

        var results: [PageResult] = []
        results.reserveCapacity(targets.count)

        for idx in targets {
            guard let page = document.page(at: idx - 1) else {
                throw RasterizeError.pageOutOfRange(idx, pageCount)
            }
            let filename = String(format: "page-%03d.png", idx)
            let pageURL = outURL.appendingPathComponent(filename)

            // Capture errors from inside autoreleasepool via an outer var.
            var captured: Error? = nil
            var result: PageResult? = nil
            autoreleasepool {
                do {
                    result = try renderPage(page, index: idx, options: opt, outURL: pageURL)
                } catch {
                    captured = error
                }
            }
            if let err = captured { throw err }
            if let r = result {
                results.append(r)
                FileHandle.standardError.write(Data(
                    "rasterize.swift: page \(idx) -> \(r.widthPx)x\(r.heightPx) (\(String(format: "%.2f", r.megapixels)) MP) -> \(r.path)\n".utf8))
            }
        }

        // stdout JSON (Backend contract).
        var pagesJSON: [[String: Any]] = []
        for r in results {
            pagesJSON.append([
                "index": r.index,
                "path": r.path,
                "width_pt": r.widthPt,
                "height_pt": r.heightPt,
                "width_px": r.widthPx,
                "height_px": r.heightPx,
                "megapixels": (r.megapixels * 100).rounded() / 100,
            ])
        }
        #if swift(>=6.0)
        let swiftVersion = "6.x"
        #elseif swift(>=5.0)
        let swiftVersion = "5.x"
        #else
        let swiftVersion = "unknown"
        #endif
        let payload: [String: Any] = [
            "backend": "pdfkit",
            "backend_version": "Darwin \(ProcessInfo.processInfo.operatingSystemVersionString) / Swift \(swiftVersion)",
            "pdf": pdfURL.path,
            "out_dir": outURL.path,
            "box": opt.boxName,
            "colorspace": opt.colorspaceName,
            "alpha": opt.alpha,
            "annots": opt.annots,
            "dpi_requested": opt.dpi,
            "page_count": pageCount,
            "pages": pagesJSON,
        ]
        let data = try JSONSerialization.data(
            withJSONObject: payload,
            options: [.prettyPrinted, .sortedKeys])
        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write(Data("\n".utf8))
        exit(0)
    } catch let err as RasterizeError {
        FileHandle.standardError.write(Data("rasterize.swift: \(err.description)\n".utf8))
        if case .usage = err {
            printUsage()
        }
        exit(err.exitCode)
    } catch {
        FileHandle.standardError.write(Data("rasterize.swift: unexpected error: \(error)\n".utf8))
        exit(1)
    }
}

main()
