import argparse
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"


class HTTPSRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        if urlparse(new_url).scheme != "https":
            raise HTTPError(new_url, code, "Refusing non-HTTPS redirect", headers, response)
        return super().redirect_request(
            request, response, code, message, headers, new_url
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download a source file into the project's raw data folder."
    )
    parser.add_argument("--url", required=True, help="HTTPS URL of the source file")
    parser.add_argument(
        "--filename", required=True, help="Filename to use inside the output folder"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Destination folder (default: data/raw/)",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Replace an existing destination file"
    )
    parser.add_argument(
        "--timeout", type=int, default=60, help="Request timeout in seconds"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    parsed_url = urlparse(args.url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise SystemExit("The source URL must use HTTPS.")

    if Path(args.filename).name != args.filename or args.filename in {".", ".."}:
        raise SystemExit("--filename must be a filename, not a path.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    destination = args.output_dir / args.filename
    if destination.exists() and not args.overwrite:
        raise SystemExit(
            f"{destination} already exists. Use --overwrite to replace it."
        )

    request = Request(args.url, headers={"User-Agent": "road-crash-severity-analysis/1.0"})
    opener = build_opener(HTTPSRedirectHandler)
    temporary_file = None
    try:
        with opener.open(request, timeout=args.timeout) as response:
            if urlparse(response.geturl()).scheme != "https":
                raise ValueError("The final download URL must use HTTPS.")
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=args.output_dir,
                prefix=f".{args.filename}.",
                suffix=".part",
                delete=False,
            ) as output:
                temporary_file = Path(output.name)
                shutil.copyfileobj(response, output)
        temporary_file.replace(destination)
    except Exception:
        if temporary_file is not None:
            temporary_file.unlink(missing_ok=True)
        raise

    print(f"Downloaded {destination} ({destination.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
