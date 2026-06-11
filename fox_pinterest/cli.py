#!/usr/bin/env python3
"""Command-line interface for Fox-Pinterest.

Usage:
    fox-pinterest login            Authenticate with Pinterest
    fox-pitchter boards            List available boards
    fox-pitchter schedule          Schedule a new pin
    fox-pitchter list-scheduled    List scheduled pins
    fox-pitchter approve           Approve a scheduled pin
    fox-pitchter publish           Publish approved pins
    fox-pitchter logout            Remove stored credentials
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .auth import login as auth_login, get_stored_token, logout as auth_logout
from .api import PinterestClient, PinterestAPIError
from .scheduler import PinScheduler
from .compliance import check_pin_content, get_attribution_text, log_compliance_action


def print_header(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_attr():
    """Print Pinterest attribution."""
    print(f"\n{get_attribution_text()}\n")


def cmd_login(args: argparse.Namespace):
    """Handle the login command."""
    app_id = args.app_id
    app_secret = args.app_secret
    redirect_uri = args.redirect_uri
    
    print_header("Pinterest Authentication")
    
    if not app_id or not app_secret:
        print("Error: --app-id and --app-secret are required.")
        print("Get these from https://developers.pinterest.com/apps/")
        print("\nOr set via environment variables:")
        print("  export PINTEREST_APP_ID=your_app_id")
        print("  export PINTEREST_APP_SECRET=your_app_secret")
        sys.exit(1)
    
    try:
        token = auth_login(app_id, app_secret, redirect_uri)
        if token:
            print("\nAuthentication successful!")
            print_attr()
    except Exception as e:
        print(f"\nAuthentication failed: {e}")
        sys.exit(1)


def cmd_boards(args: argparse.Namespace):
    """Handle the boards command."""
    print_header("Pinterest Boards")
    
    token = get_stored_token()
    if not token:
        print("Not authenticated. Run 'fox-pinterest login' first.")
        sys.exit(1)
    
    try:
        client = PinterestClient(token)
        user = client.get_user()
        print(f"Account: {user.get('username', 'Unknown')}")
        
        boards = client.list_boards()
        items = boards.get("items", [])
        
        if not items:
            print("\nNo boards found.")
        else:
            print(f"\nFound {len(items)} board(s):\n")
            for board in items:
                print(f"  {board.get('id')}")
                print(f"    Name:     {board.get('name')}")
                print(f"    Privacy:  {board.get('privacy')}")
                print(f"    Pins:     {board.get('pin_count', 0)}")
                print()
        
        print_attr()
    except PinterestAPIError as e:
        print(f"API error: {e}")
        sys.exit(1)


def cmd_schedule(args: argparse.Namespace):
    """Handle the schedule command."""
    print_header("Schedule a Pin")
    
    token = get_stored_token()
    if not token:
        print("Not authenticated. Run 'fox-pinterest login' first.")
        sys.exit(1)
    
    # Validate inputs
    if not args.image:
        print("Error: --image is required.")
        sys.exit(1)
    if not args.board_id:
        print("Error: --board-id is required. Use 'boards' command to list boards.")
        sys.exit(1)
    if not args.link:
        print("Error: --link is required (e.g., Etsy listing URL).")
        sys.exit(1)
    
    title = args.title or ""
    description = args.description or ""
    
    # Compliance check on pin content
    compliance = check_pin_content(title, description)
    if not compliance.is_compliant:
        print("\n⚠  Compliance warnings:")
        for issue in compliance.issues:
            print(f"    - {issue}")
        if not args.force:
            print("\n  Use --force to override compliance warnings.")
            sys.exit(1)
    
    # Schedule the pin
    scheduler = PinScheduler()
    scheduled_pin = scheduler.schedule(
        board_id=args.board_id,
        image_path=args.image,
        title=title,
        description=description,
        link=args.link,
        scheduled_time=args.scheduled_time or "",
    )
    
    print(f"\nPin scheduled (internal ID: {scheduled_pin.created_at})")
    print(f"  Title:      {title or '(none)'}")
    print(f"  Board:      {args.board_id}")
    print(f"  Link:       {args.link}")
    print(f"  Image:      {args.image}")
    print(f"  Scheduled:  {args.scheduled_time or '(immediate)'}")
    print(f"  Approved:   No — use 'approve' to mark for publication")
    print_attr()


def cmd_list_scheduled(args: argparse.Namespace):
    """Handle the list-scheduled command."""
    print_header("Scheduled Pins")
    
    scheduler = PinScheduler()
    pins = scheduler.list_scheduled()
    
    if not pins:
        print("\nNo pins scheduled.")
    else:
        for i, pin in enumerate(pins):
            status = "APPROVED" if pin.approved else "PENDING"
            print(f"\n  [{i}] {pin.title or '(untitled)'}")
            print(f"      Board:   {pin.board_id}")
            print(f"      Link:    {pin.link}")
            print(f"      Image:   {pin.image_path}")
            print(f"      Status:  {status}")
            print(f"      Time:    {pin.scheduled_time or '(no schedule)'}")
    
    print_attr()


def cmd_approve(args: argparse.Namespace):
    """Handle the approve command."""
    print_header("Approve Pin")
    
    if args.pin_index is None:
        print("Error: --pin-index is required. Use 'list-scheduled' to see available pins.")
        sys.exit(1)
    
    scheduler = PinScheduler()
    pin = scheduler.approve_by_index(args.pin_index)
    
    if pin:
        print(f"\nPin approved for publication:")
        print(f"  Title:  {pin.title}")
        print(f"  Board:  {pin.board_id}")
        print(f"  Link:   {pin.link}")
        print_attr()
    else:
        print(f"\nNo pin found at index {args.pin_index}.")
        sys.exit(1)


def cmd_publish(args: argparse.Namespace):
    """Handle the publish command."""
    print_header("Publish Approved Pins")
    
    token = get_stored_token()
    if not token:
        print("Not authenticated. Run 'fox-pinterest login' first.")
        sys.exit(1)
    
    client = PinterestClient(token)
    scheduler = PinScheduler()
    
    approved_pins = [
        p for p in scheduler.list_scheduled()
        if p.approved and not p.pin_id  # Not yet published
    ]
    
    if not approved_pins:
        print("\nNo approved pins ready for publication.")
        print("Schedule pins with 'schedule', then approve them with 'approve'.")
        return
    
    print(f"\nPublishing {len(approved_pins)} pin(s)...\n")
    
    for i, pin in enumerate(approved_pins, 1):
        log_compliance_action(
            "publish",
            f"Pin {i}/{len(approved_pins)}: '{pin.title or '(untitled)'}' → board {pin.board_id}"
        )
        
        try:
            # Upload media and create pin
            media_response = client.upload_media(pin.image_path)
            media_id = media_response.get("media_source", {}).get("media_id", "")
            
            result = client.create_pin(
                board_id=pin.board_id,
                media_source={"media_id": media_id},
                link=pin.link,
                title=pin.title,
                description=pin.description,
            )
            
            pin_id = result.get("id", "unknown")
            print(f"  ✓ Published: {pin.title or '(untitled)'} (ID: {pin_id})")
            
        except PinterestAPIError as e:
            print(f"  ✗ Failed: {pin.title or '(untitled)'} — {e}")
        except Exception as e:
            print(f"  ✗ Failed: {pin.title or '(untitled)'} — {e}")
    
    print_attr()


def cmd_logout(args: argparse.Namespace):
    """Handle the logout command."""
    print_header("Logout")
    auth_logout()
    print_attr()


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="fox-pinterest",
        description="Pinterest Pin scheduler and content management tool for Etsy merchants.",
    )
    parser.add_argument(
        "--app-id",
        help="Pinterest app ID (or set PINTEREST_APP_ID env var)",
    )
    parser.add_argument(
        "--app-secret",
        help="Pinterest app secret (or set PINTEREST_APP_SECRET env var)",
    )
    parser.add_argument(
        "--redirect-uri",
        default="https://localhost:8080/callback",
        help="OAuth redirect URI (default: https://localhost:8080/callback)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Override compliance warnings",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Login
    login_parser = subparsers.add_parser("login", help="Authenticate with Pinterest")
    login_parser.set_defaults(func=cmd_login)
    
    # Boards
    boards_parser = subparsers.add_parser("boards", help="List boards")
    boards_parser.set_defaults(func=cmd_boards)
    
    # Schedule
    schedule_parser = subparsers.add_parser("schedule", help="Schedule a pin")
    schedule_parser.add_argument("--image", required=True, help="Path to pin image")
    schedule_parser.add_argument("--board-id", required=True, help="Target board ID")
    schedule_parser.add_argument("--title", default="", help="Pin title")
    schedule_parser.add_argument("--description", default="", help="Pin description")
    schedule_parser.add_argument("--link", required=True, help="Destination URL (Etsy listing)")
    schedule_parser.add_argument("--scheduled-time", default="", help="ISO 8601 datetime")
    schedule_parser.set_defaults(func=cmd_schedule)
    
    # List scheduled
    list_parser = subparsers.add_parser("list-scheduled", help="List scheduled pins")
    list_parser.set_defaults(func=cmd_list_scheduled)
    
    # Approve
    approve_parser = subparsers.add_parser("approve", help="Approve a scheduled pin")
    approve_parser.add_argument(
        "--pin-index", type=int, required=True, help="Index of pin from list-scheduled"
    )
    approve_parser.set_defaults(func=cmd_approve)
    
    # Publish
    publish_parser = subparsers.add_parser("publish", help="Publish approved pins")
    publish_parser.set_defaults(func=cmd_publish)
    
    # Logout
    logout_parser = subparsers.add_parser("logout", help="Remove stored credentials")
    logout_parser.set_defaults(func=cmd_logout)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
