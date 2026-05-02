{
  description = "Google Photos Migration Tool";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3.withPackages (ps: with ps; [
          google-api-python-client
          google-auth-oauthlib
          requests
          click
          remotezip
          pytest
          pytest-mock
          pytest-cov
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            python
            pkgs.poetry
          ];
          shellHook = ''
            export PYTHONPATH=$PYTHONPATH:$(pwd)
            echo "Google Data Migration Suite dev environment loaded with all dependencies (via Nixpkgs)."
          '';
        };

        packages.default = pkgs.python3.pkgs.buildPythonApplication {
          pname = "gphoto-migrate";
          version = "0.1.0";
          src = ./.;
          format = "pyproject";
          nativeBuildInputs = [ pkgs.python3Packages.poetry-core ];
          propagatedBuildInputs = with pkgs.python3Packages; [
            google-api-python-client
            google-auth-oauthlib
            requests
            click
            remotezip
            setuptools
          ];
        };
      });
}
