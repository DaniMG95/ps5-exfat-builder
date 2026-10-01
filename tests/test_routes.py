import unittest

from ps5_exfat_builder.formats.routes import default_routes, route_map


class RouteTests(unittest.TestCase):
    def test_existing_conversion_routes_are_declared_as_legacy(self):
        routes = route_map()

        self.assertEqual(routes[("exfat", "ffpkg")].status, "legacy")
        self.assertEqual(routes[("ffpkg", "exfat")].status, "legacy")

    def test_future_ampr_and_pkg_routes_are_declared(self):
        routes = route_map()

        self.assertEqual(routes[("folder", "ampr")].status, "planned")
        self.assertEqual(routes[("pkg", "ampr")].status, "planned")
        self.assertEqual(routes[("ampr", "folder")].status, "planned")
        self.assertEqual(routes[("ampr", "pkg")].status, "planned")
        self.assertEqual(routes[("exfat", "pkg")].status, "planned")

    def test_route_keys_are_unique(self):
        routes = default_routes()

        self.assertEqual(len(routes), len({route.key for route in routes}))


if __name__ == "__main__":
    unittest.main()
