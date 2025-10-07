def main() -> None:
    from src.utils.common import configure_logging
    configure_logging()
    from src.ui.app import run_app
    run_app()


if __name__ == "__main__":
    main()
