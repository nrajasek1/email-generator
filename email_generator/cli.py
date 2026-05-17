from __future__ import annotations

import argparse

from email_generator.core import generate_email
from email_generator.schemas import EmailRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a plain-text email subject and body."
    )
    parser.add_argument("--purpose", required=True, help="Why the email is being written.")
    parser.add_argument("--tone", required=True, help="Desired writing tone.")
    parser.add_argument("--context", required=True, help="Supporting details for the email.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = generate_email(
        EmailRequest(
            purpose=args.purpose,
            tone=args.tone,
            context=args.context,
        )
    )

    print("Subject:")
    print(result.subject)
    print()
    print("Body:")
    print(result.body)


if __name__ == "__main__":
    main()
