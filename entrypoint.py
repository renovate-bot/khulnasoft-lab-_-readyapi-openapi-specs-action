import importlib
import json
import os
import sys
from typing import Optional

import yaml
from readyapi.openapi.utils import get_openapi


def get_env_variable(var_name: str, required: bool = False, default: Optional[str] = None) -> Optional[str]:
    """Fetches an environment variable with optional default and validation."""
    value = os.environ.get(var_name)
    if required and not value:
        raise ValueError(f"Environment variable '{var_name}' is required but not set.")
    return value or default


def append_to_python_path(path: str) -> None:
    """Adds a directory to the Python path."""
    if path and os.path.isdir(path):
        sys.path.append(path)
    else:
        raise FileNotFoundError(f"The specified path '{path}' does not exist or is not a directory.")


def install_dependencies(command: Optional[str]) -> None:
    """Installs dependencies using the provided shell command."""
    if command:
        exit_code = os.system(command)
        if exit_code != 0:
            raise RuntimeError(f"Dependency installation failed with exit code {exit_code}.")


def import_module(directory: str, module_name: str):
    """Dynamically imports a Python module."""
    try:
        return importlib.import_module(f"{directory}.{module_name}")
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            f"Error importing module '{directory}/{module_name}'. Check if paths and file names are correct. "
            f"Details: {e}"
        )


def get_readyapi_app(module, app_name: str):
    """Retrieves the ReadyAPI app object from a module."""
    try:
        return getattr(module, app_name)
    except AttributeError as e:
        raise AttributeError(f"Module does not contain the application object '{app_name}'. Details: {e}")


def find_versioned_app(app, version: str):
    """Finds the versioned app based on the provided version."""
    for route in app.router.routes:
        if version in route.path:
            return route.app
    raise ValueError(f"No route found matching the specified version '{version}'.")


def write_output_file(file_name: str, content: dict, file_format: str):
    """Writes the OpenAPI specs to a file in the specified format."""
    with open(file_name, "w") as f:
        if file_format == "json":
            json.dump(content, f, indent=2)
        elif file_format == "yaml":
            yaml.dump(content, f, default_flow_style=False)
        else:
            raise ValueError("Invalid file format. Only 'yaml' or 'json' are supported.")


def main():
    # Set up environment variables
    workspace = get_env_variable("GITHUB_WORKSPACE", required=True)
    append_to_python_path(workspace)

    install_command = get_env_variable("INPUT_INSTALLDEPENDENCIES")
    module_dir = get_env_variable("INPUT_MODULEDIR", required=True)
    file_name = get_env_variable("INPUT_FILENAME", required=True)
    app_name = get_env_variable("INPUT_APPNAME", required=True)
    version = get_env_variable("INPUT_READYAPIVERSIONING")
    output_name = get_env_variable("INPUT_OUTPUTNAME", required=True)
    output_extension = get_env_variable("INPUT_OUTPUTEXTENSION", required=True).lower()

    if ".py" in file_name:
        file_name = file_name.replace(".py", "")

    # Install dependencies if necessary
    install_dependencies(install_command)

    # Import module and retrieve app
    module = import_module(module_dir, file_name)
    app = get_readyapi_app(module, app_name)

    # Find versioned app if a version is specified
    if version:
        app = find_versioned_app(app, version)

    # Generate OpenAPI specs
    specs = get_openapi(
        title=getattr(app, "title", None),
        version=getattr(app, "version", None),
        openapi_version=getattr(app, "openapi_version", None),
        description=getattr(app, "description", None),
        routes=getattr(app, "routes", None),
    )

    # Write specs to output file
    output_file = f"{output_name}.{output_extension}"
    write_output_file(output_file, specs, output_extension)
    print(f"OpenAPI specifications successfully written to {output_file}.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
