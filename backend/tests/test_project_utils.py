import unittest

from fbuild_backend.utils.projects import derive_project_name, slugify_project_name


class ProjectUtilsTest(unittest.TestCase):
    def test_derive_project_name_strips_git_suffix(self) -> None:
        self.assertEqual(derive_project_name("https://github.com/acme/mobile-app.git"), "mobile-app")

    def test_derive_project_name_keeps_last_segment_without_suffix(self) -> None:
        self.assertEqual(derive_project_name("git@github.com:acme/mobile_app"), "mobile_app")

    def test_slugify_replaces_non_alphanumeric_segments(self) -> None:
        self.assertEqual(slugify_project_name(" Mobile App_Admin "), "mobile-app-admin")

    def test_slugify_falls_back_when_empty(self) -> None:
        self.assertEqual(slugify_project_name("%%%"), "project")


if __name__ == "__main__":
    unittest.main()
