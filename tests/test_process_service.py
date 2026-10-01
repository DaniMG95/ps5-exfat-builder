import unittest

from ps5_exfat_builder.services.process import ProcessPerformance


class ProcessServiceTests(unittest.TestCase):
    def test_maximum_performance_sets_thread_environment(self):
        perf = ProcessPerformance(priority="high", use_all_cpus=True, worker_count=12)

        env = perf.env_overrides()

        self.assertEqual(env["OMP_NUM_THREADS"], "12")
        self.assertEqual(env["OPENBLAS_NUM_THREADS"], "12")
        self.assertEqual(env["MKL_NUM_THREADS"], "12")
        self.assertEqual(env["UV_THREADPOOL_SIZE"], "12")
        self.assertEqual(env["PS5_EXFAT_WORKERS"], "12")

    def test_normal_performance_has_no_thread_environment(self):
        self.assertEqual(ProcessPerformance().env_overrides(), {})


if __name__ == "__main__":
    unittest.main()
