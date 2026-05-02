{
  description = "Google Photos Migration Tool";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, pyproject-nix, uv2nix, pyproject-build-systems }:
    let
      inherit (nixpkgs) lib;
      forAllSystems = lib.genAttrs lib.systems.flakeExposed;

      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      overlay = workspace.mkPyprojectOverlay {
        sourcePreference = "wheel";
      };

      editableOverlay = workspace.mkEditablePyprojectOverlay {
        root = "$REPO_ROOT";
      };

      # Function to create a Python package set
      mkPythonSet = pkgs: python: extensions:
        (pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        }).overrideScope (lib.composeManyExtensions extensions);

      # Get package name from pyproject.toml
      pyproject = lib.importTOML ./pyproject.toml;
      packageName = pyproject.project.name;

    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          pythonSet = mkPythonSet pkgs pkgs.python312 [
            pyproject-build-systems.overlays.wheel
            overlay
          ];

          # Create the runtime application environment
          app = pythonSet.mkVirtualEnv "${packageName}-env" workspace.deps.default;

          # Create a development/testing environment containing all tools
          # We include pkgs.pyright separately as it's better packaged in Nix
          checkEnv = pythonSet.mkVirtualEnv "${packageName}-check-env" workspace.deps.all;

        in
        {
          # The default package is a validated version of the app
          default = pkgs.stdenv.mkDerivation {
            pname = packageName;
            version = pyproject.project.version;
            src = ./.;

            nativeBuildInputs = [ 
              checkEnv
              pkgs.pyright
            ];

            buildPhase = ''
              export PYTHONPATH=$PYTHONPATH:$(pwd)/src
              
              # Ensure we use pkgs.pyright, not the one from checkEnv
              # We can do this by putting pkgs.pyright earlier in PATH or explicitly calling it
              PYRIGHT_BIN=${pkgs.pyright}/bin/pyright
              
              echo "Running quality checks..."
              
              echo "Linting with ruff..."
              ruff check src tests
              
              echo "Type checking with mypy..."
              mypy src tests
              
              echo "Type checking with pyright..."
              $PYRIGHT_BIN src tests
              
              echo "Running unit tests with pytest..."
              pytest
            '';

            installPhase = ''
              mkdir -p $out
              cp -r ${app}/* $out/
            '';

            meta = {
              description = pyproject.project.description;
              mainProgram = "gphoto-migrate";
            };
          };

          # Raw app environment without checks
          app-raw = app;
        }
      );

      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          pythonSet = (mkPythonSet pkgs pkgs.python312 [
            pyproject-build-systems.overlays.wheel
            overlay
          ]).overrideScope editableOverlay;

          virtualenv = pythonSet.mkVirtualEnv "${packageName}-dev-env" workspace.deps.all;
        in
        {
          default = pkgs.mkShell {
            packages = [
              virtualenv
              pkgs.uv
              pkgs.pyright
            ];
            env = {
              UV_NO_SYNC = "1";
              UV_PYTHON = pythonSet.python.interpreter;
              UV_PYTHON_DOWNLOADS = "never";
            };
            shellHook = ''
              export REPO_ROOT=$(git rev-parse --show-toplevel)
              export PYTHONPATH=$PYTHONPATH:$(pwd)/src
            '';
          };
        }
      );
    };
}
