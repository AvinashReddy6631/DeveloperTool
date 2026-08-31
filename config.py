import os

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


def env_value(name, default=None):
    value = os.getenv(name, default)
    if value is None:
        return None
    return str(value).strip().strip('"').strip("'")


# ============================================================
# CONFIGURATION
# ============================================================

OPENROUTER_API_KEY = env_value(
    "OPENROUTER_API_KEY"
)

DB_HOST = env_value(
    "DB_HOST"
)

DB_NAME = env_value(
    "DB_NAME"
)

DB_USER = env_value(
    "DB_USER"
)

DB_PASSWORD = env_value(
    "DB_PASSWORD"
)

DB_PORT = int(
    env_value(
        "DB_PORT",
        "5432"
    )
)


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

APP_HOST = os.getenv(
    "APP_HOST",
    "127.0.0.1"
)

APP_PORT = int(
    os.getenv(
        "APP_PORT",
        "8000"
    )
)

APP_ENV = os.getenv(
    "APP_ENV",
    "development"
)


# ============================================================
# VALIDATION
# ============================================================

def validate_configuration(
    require_llm=False,
    require_database=True
):

    errors = []

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    if require_database:

        database_variables = {
            "DB_HOST": DB_HOST,
            "DB_NAME": DB_NAME,
            "DB_USER": DB_USER,
            "DB_PASSWORD": DB_PASSWORD
        }

        for name, value in database_variables.items():

            if not value:

                errors.append(
                    f"Missing environment variable: {name}"
                )

        if not DB_PORT:

            errors.append(
                "Invalid DB_PORT."
            )

    # --------------------------------------------------------
    # LLM
    # --------------------------------------------------------

    if require_llm:

        if not OPENROUTER_API_KEY:

            errors.append(
                "Missing environment variable: "
                "OPENROUTER_API_KEY"
            )

    # --------------------------------------------------------
    # Raise configuration error
    # --------------------------------------------------------

    if errors:

        raise RuntimeError(
            "Configuration validation failed:\n"
            + "\n".join(
                f"- {error}"
                for error in errors
            )
        )

    return True


# ============================================================
# SAFE CONFIGURATION SUMMARY
# ============================================================

def configuration_summary():

    return {

        "environment": APP_ENV,

        "host": APP_HOST,

        "port": APP_PORT,

        "database": {

            "host": DB_HOST,

            "database": DB_NAME,

            "user": DB_USER,

            "port": DB_PORT,

            "password_configured":
                bool(DB_PASSWORD)
        },

        "openrouter": {

            "api_key_configured":
                bool(OPENROUTER_API_KEY)
        }
    }


# ============================================================
# DEVELOPMENT TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("MCP CONFIGURATION")
    print("=" * 60)

    try:

        validate_configuration(
            require_llm=False,
            require_database=True
        )

        print()
        print("Configuration: VALID")

        print()
        print(
            configuration_summary()
        )

    except Exception as error:

        print()
        print(
            "Configuration: INVALID"
        )

        print()
        print(
            error
        )

    print()
    print("=" * 60)