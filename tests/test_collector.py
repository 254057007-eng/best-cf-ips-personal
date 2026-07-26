import importlib.util
import ipaddress
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


COLLECTOR = load_module(
    'best_cf_ipv4_collector',
    ROOT / 'scripts' / 'best-cf-ipv4-collector.py',
)
VALIDATOR = load_module(
    'validate_output',
    ROOT / 'scripts' / 'validate_output.py',
)

EXPECTED_SOURCES = {
    'https://www.wetest.vip/page/cloudfront/address_v4.html': 'WeTest',
    'https://api.uouin.com/cloudflare.html': 'UOUIN',
    'https://bestcf.pages.dev/xinyitang3/ipv4.txt': 'Mia',
    'https://bestcf.pages.dev/tiancheng/all.txt': 'Tiancheng',
    'https://raw.githubusercontent.com/gslege/CloudflareIP/refs/heads/main/SG.txt': 'Gslege-SG',
    'https://raw.githubusercontent.com/gslege/CloudflareIP/refs/heads/main/DE.txt': 'Gslege-DE',
    'https://raw.githubusercontent.com/gslege/CloudflareIP/refs/heads/main/US.txt': 'Gslege-US',
    'https://raw.githubusercontent.com/ymyuuu/IPDB/refs/heads/main/BestCF/bestcfv4.txt': 'IPDB',
    'https://vps789.com/openApi/cfIpApi': 'VPS789',
    'https://api.4ce.cn/api/bestCFIP': 'vvhan',
}


class CollectorTests(unittest.TestCase):
    def test_sources_match_reference_commit(self):
        self.assertEqual(COLLECTOR.SOURCES, EXPECTED_SOURCES)

    def test_extracts_arbitrary_text_and_validates_ipv4(self):
        text = (
            'HTML 1.1.1.1 JSON {"ip":"8.8.8.8"} '
            'invalid 999.1.1.1 duplicate 1.1.1.1'
        )
        self.assertEqual(
            COLLECTOR.extract_ipv4(text),
            {'1.1.1.1', '8.8.8.8'},
        )

    def test_fixed_port_and_retry_strategy(self):
        self.assertEqual(COLLECTOR.PORT, '443')
        session = COLLECTOR._session()
        retry = session.get_adapter('https://').max_retries
        self.assertEqual(retry.total, 3)
        self.assertEqual(retry.backoff_factor, 2.0)
        self.assertEqual(
            retry.status_forcelist,
            {429, 500, 502, 503, 504},
        )
        session.close()

    def test_beijing_timestamp_format(self):
        self.assertRegex(
            COLLECTOR.beijing_timestamp(),
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$',
        )

    def test_valid_output_contract(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / 'best-cf-ipv4.txt'
            path.write_text(
                'bestips updated at#2026-07-26 12:34\n'
                '1.1.1.1:443#AU\n'
                '8.8.8.8:443#US\n',
                encoding='utf-8',
            )
            result = VALIDATOR.validate_pool(path, min_count=2)
            self.assertEqual(result['ipv4Count'], 2)
            self.assertTrue(result['allPorts443'])

    def test_validator_rejects_duplicate_and_non_global_ipv4(self):
        cases = [
            (
                'bestips updated at#2026-07-26 12:34\n'
                '1.1.1.1:443#AU\n'
                '1.1.1.1:443#AU\n'
            ),
            (
                'bestips updated at#2026-07-26 12:34\n'
                '10.0.0.1:443#XX\n'
            ),
        ]
        for content in cases:
            with self.subTest(content=content):
                with tempfile.TemporaryDirectory() as temp_dir:
                    path = Path(temp_dir) / 'best-cf-ipv4.txt'
                    path.write_text(content, encoding='utf-8')
                    with self.assertRaises(ValueError):
                        VALIDATOR.validate_pool(path)

    def test_all_expected_source_examples_are_global_ipv4(self):
        for ip in ('1.1.1.1', '8.8.8.8', '104.16.0.1'):
            address = ipaddress.ip_address(ip)
            self.assertEqual(address.version, 4)
            self.assertTrue(address.is_global)


if __name__ == '__main__':
    unittest.main()
