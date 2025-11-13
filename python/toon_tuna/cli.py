"""
Command-line interface for toon-tuna
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from . import encode, decode, encode_optimal, estimate_savings, EncodeOptions


def auto_detect_format(file_path: Path) -> str:
    """Auto-detect format based on file extension."""
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        return "json"
    elif suffix in [".toon", ".tn"]:
        return "toon"
    else:
        # Try to detect from content
        try:
            content = file_path.read_text()
            json.loads(content)
            return "json"
        except (json.JSONDecodeError, ValueError):
            return "toon"


def read_input(input_path: Optional[str]) -> str:
    """Read input from file or stdin."""
    if input_path and input_path != "-":
        return Path(input_path).read_text()
    else:
        return sys.stdin.read()


def write_output(output: str, output_path: Optional[str]) -> None:
    """Write output to file or stdout."""
    if output_path and output_path != "-":
        Path(output_path).write_text(output)
    else:
        print(output)


def create_encode_options(args) -> EncodeOptions:
    """Create EncodeOptions from CLI arguments."""
    return EncodeOptions(
        delimiter=args.delimiter,
        indent=args.indent,
        use_length_markers=args.length_marker,
        strict=args.strict,
    )


def cmd_encode(args):
    """Encode JSON to TOON format."""
    input_data = read_input(args.input)

    try:
        data = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    options = create_encode_options(args)

    try:
        result = encode(data, options)
        write_output(result, args.output)
    except Exception as e:
        print(f"Error encoding: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_decode(args):
    """Decode TOON to JSON format."""
    input_data = read_input(args.input)

    try:
        data = decode(input_data)
        result = json.dumps(data, indent=2 if args.pretty else None, ensure_ascii=False)
        write_output(result, args.output)
    except Exception as e:
        print(f"Error decoding: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_optimize(args):
    """Smart format selection - choose optimal format."""
    input_data = read_input(args.input)

    try:
        data = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    options = create_encode_options(args)

    try:
        result = encode_optimal(data, tokenizer=args.tokenizer, options=options)

        if args.compare_all:
            # Show comparison
            print("=" * 60, file=sys.stderr)
            print(f"Format: {result['format'].upper()}", file=sys.stderr)
            print(f"TOON tokens: {result['toon_tokens']}", file=sys.stderr)
            print(f"JSON tokens: {result['json_tokens']}", file=sys.stderr)
            print(f"Savings: {result['savings_percent']:.2f}%", file=sys.stderr)
            print(f"Reason: {result['recommendation_reason']}", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            print(file=sys.stderr)

        write_output(result["data"], args.output)

        if args.stats_file:
            stats = {
                "format": result["format"],
                "toon_tokens": result["toon_tokens"],
                "json_tokens": result["json_tokens"],
                "savings_percent": result["savings_percent"],
                "recommendation_reason": result["recommendation_reason"],
            }
            Path(args.stats_file).write_text(json.dumps(stats, indent=2))

    except Exception as e:
        print(f"Error optimizing: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_estimate(args):
    """Estimate token savings between formats."""
    input_data = read_input(args.input)

    try:
        data = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    options = create_encode_options(args)

    try:
        result = estimate_savings(data, tokenizer=args.tokenizer, options=options)

        print(f"JSON tokens: {result['json_tokens']}")
        print(f"TOON tokens: {result['toon_tokens']}")
        print(f"Savings: {result['savings']} tokens ({result['savings_percent']:.2f}%)")
        print(f"Recommended format: {result['recommended_format'].upper()}")

    except Exception as e:
        print(f"Error estimating: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="tuna",
        description="Smart TOON/JSON optimizer for LLMs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Encode JSON to TOON
  tuna encode data.json -o output.toon

  # Decode TOON to JSON
  tuna decode data.toon -o output.json

  # Smart optimization (recommended!)
  tuna optimize data.json -o optimized.txt --compare-all

  # Estimate savings
  tuna estimate data.json

  # Use with pipes
  echo '{"users":[{"id":1,"name":"Alice"}]}' | tuna optimize

  # Custom delimiter
  tuna encode data.json --delimiter '|' -o output.toon
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("input", nargs="?", help="Input file (or - for stdin)")
    common_parser.add_argument("-o", "--output", help="Output file (or - for stdout)")

    # Encoding options
    encode_parser = argparse.ArgumentParser(add_help=False)
    encode_parser.add_argument(
        "--delimiter",
        default=",",
        choices=[",", "\t", "|"],
        help="Delimiter for arrays (default: ,)",
    )
    encode_parser.add_argument(
        "--indent", type=int, default=2, help="Indentation spaces (default: 2)"
    )
    encode_parser.add_argument(
        "--no-length-marker",
        dest="length_marker",
        action="store_false",
        help="Disable length markers in arrays",
    )
    encode_parser.add_argument(
        "--no-strict", dest="strict", action="store_false", help="Disable strict mode"
    )

    # Encode command
    encode_cmd = subparsers.add_parser(
        "encode",
        parents=[common_parser, encode_parser],
        help="Encode JSON to TOON format",
    )
    encode_cmd.set_defaults(func=cmd_encode)

    # Decode command
    decode_cmd = subparsers.add_parser(
        "decode", parents=[common_parser], help="Decode TOON to JSON format"
    )
    decode_cmd.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output"
    )
    decode_cmd.set_defaults(func=cmd_decode)

    # Optimize command (smart selection)
    optimize_cmd = subparsers.add_parser(
        "optimize",
        parents=[common_parser, encode_parser],
        help="Smart format selection (recommended!)",
    )
    optimize_cmd.add_argument(
        "--tokenizer",
        default="cl100k_base",
        help="Tokenizer to use (default: cl100k_base for GPT-4)",
    )
    optimize_cmd.add_argument(
        "--compare-all",
        action="store_true",
        help="Show comparison of both formats to stderr",
    )
    optimize_cmd.add_argument(
        "--stats-file", help="Write statistics to JSON file"
    )
    optimize_cmd.set_defaults(func=cmd_optimize)

    # Estimate command
    estimate_cmd = subparsers.add_parser(
        "estimate",
        parents=[common_parser, encode_parser],
        help="Estimate token savings",
    )
    estimate_cmd.add_argument(
        "--tokenizer",
        default="cl100k_base",
        help="Tokenizer to use (default: cl100k_base for GPT-4)",
    )
    estimate_cmd.set_defaults(func=cmd_estimate)

    # Auto-detect mode (no subcommand)
    parser.add_argument("file", nargs="?", help="Input file (auto-detect format)")
    parser.add_argument("-o", "--output", help="Output file")
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Use smart format selection",
    )
    parser.add_argument(
        "--delimiter",
        default=",",
        choices=[",", "\t", "|"],
        help="Delimiter for arrays (default: ,)",
    )
    parser.add_argument(
        "--indent", type=int, default=2, help="Indentation spaces (default: 2)"
    )
    parser.add_argument(
        "--no-length-marker",
        dest="length_marker",
        action="store_false",
        help="Disable length markers",
    )
    parser.add_argument(
        "--no-strict", dest="strict", action="store_false", help="Disable strict mode"
    )
    parser.add_argument(
        "--compare-all",
        action="store_true",
        help="Show comparison (with --optimize)",
    )
    parser.add_argument(
        "--tokenizer",
        default="cl100k_base",
        help="Tokenizer (with --optimize)",
    )

    args = parser.parse_args()

    # If no command specified, use auto-detect mode
    if not args.command:
        if args.optimize:
            # Treat as optimize command
            if not hasattr(args, "input"):
                args.input = args.file
            args.func = cmd_optimize
            args.stats_file = None
            args.func(args)
        elif args.file:
            # Auto-detect based on file extension
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File not found: {args.file}", file=sys.stderr)
                sys.exit(1)

            fmt = auto_detect_format(file_path)
            args.input = args.file

            if fmt == "json":
                # Encode to TOON
                args.func = cmd_encode
            else:
                # Decode to JSON
                args.func = cmd_decode
                args.pretty = True

            args.func(args)
        else:
            parser.print_help()
            sys.exit(1)
    else:
        # Run the specified command
        if hasattr(args, "func"):
            args.func(args)
        else:
            parser.print_help()
            sys.exit(1)


if __name__ == "__main__":
    main()
