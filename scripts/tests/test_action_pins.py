import unittest

from scripts.check_action_pins import check_action, check_workflow


class ActionPinsTest(unittest.TestCase):
    sha = "a" * 40
    image = "ghcr.io/org/runner@sha256:" + "b" * 64

    def test_workflow_accepts_immutable_and_local_references(self):
        workflow = {"jobs": {
            "call": {"uses": f"org/repo/.github/workflows/call.yml@{self.sha}"},
            "run": {
                "container": {"image": self.image},
                "services": {"database": {"image": self.image}},
                "steps": [
                    {"uses": f"org/repo@{self.sha}"},
                    {"uses": "./.github/actions/example"},
                    {"uses": f"docker://{self.image}"},
                ],
            },
        }}
        self.assertEqual(list(check_workflow(workflow)), [])

    def test_workflow_rejects_mutable_references(self):
        for ref in ("v2", "main", self.sha[:12]):
            with self.subTest(ref=ref):
                workflow = {"jobs": {
                    "call": {"uses": f"org/repo/.github/workflows/call.yml@{ref}"},
                    "run": {"steps": [{"uses": f"org/repo@{ref}"}]},
                }}
                self.assertEqual(len(list(check_workflow(workflow))), 2)

    def test_docker_requires_digest(self):
        workflow = {"jobs": {"run": {
            "container": "node:26",
            "services": {"database": {"image": "redis:latest"}},
            "steps": [{"uses": "docker://alpine:3"}],
        }}}
        self.assertEqual(len(list(check_workflow(workflow))), 3)
        self.assertEqual(list(check_action({
            "runs": {"using": "docker", "image": "Dockerfile"},
        })), [])
        self.assertEqual(len(list(check_action({
            "runs": {"using": "docker", "image": "docker://alpine:3"},
        }))), 1)

    def test_composite_steps_require_immutable_refs(self):
        action = {"runs": {"using": "composite", "steps": [
            {"uses": "org/repo@v2"},
            {"uses": f"org/repo@{self.sha}"},
            {"run": "echo ok"},
        ]}}
        self.assertEqual(len(list(check_action(action))), 1)


if __name__ == "__main__":
    unittest.main()
