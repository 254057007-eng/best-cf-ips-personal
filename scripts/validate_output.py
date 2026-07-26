import argparse
import ipaddress
import json
import re
from pathlib import Path


HEADER_PATTERN = re.compile(
    r'^bestips updated at#\d{4}-\d{2}-\d{2} \d{2}:\d{2}$'
)
ENTRY_PATTERN = re.compile(
    r'^(\d{1,3}(?:\.\d{1,3}){3}):443#([A-Z]{2})$'
)


def validate_pool(path: Path, min_count: int = 1) -> dict[str, object]:
    """Validate the complete address-pool contract."""
    lines = path.read_text(encoding='utf-8').splitlines()
    if not lines or not HEADER_PATTERN.fullmatch(lines[0]):
        raise ValueError('invalid_header')

    seen: set[str] = set()
    xx_count = 0
    for line_number, line in enumerate(lines[1:], start=2):
        match = ENTRY_PATTERN.fullmatch(line)
        if not match:
            raise ValueError(f'invalid_entry_at_line_{line_number}')

        ip = ipaddress.ip_address(match.group(1))
        if ip.version != 4:
            raise ValueError(f'non_ipv4_at_line_{line_number}')
        if not ip.is_global:
            raise ValueError(f'non_global_ipv4_at_line_{line_number}')

        normalized = str(ip)
        if normalized in seen:
            raise ValueError(f'duplicate_ipv4_at_line_{line_number}')
        seen.add(normalized)
        if match.group(2) == 'XX':
            xx_count += 1

    if len(seen) < min_count:
        raise ValueError(
            f'pool_too_small_{len(seen)}_minimum_{min_count}'
        )

    return {
        'header': lines[0],
        'ipv4Count': len(seen),
        'xxCount': xx_count,
        'countryLookupSuccessCount': len(seen) - xx_count,
        'allPorts443': True,
        'duplicateCount': 0,
        'invalidOrNonGlobalCount': 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=Path)
    parser.add_argument('--min-count', type=int, default=1)
    args = parser.parse_args()
    result = validate_pool(args.path, args.min_count)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
