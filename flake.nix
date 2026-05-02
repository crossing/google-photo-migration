{
  description = "Google Photos Migration Tool";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication mkPoetryEnv;

        python = pkgs.python311;

        pythonEnv = mkPoetryEnv {
          projectDir = ./.;
          python = python;
          preferWheels = true;
        };
      in
      {
        packages.default = mkPoetryApplication {
          projectDir = ./.;
          python = python;
          preferWheels = true;
        };

        devShells.default = pkgs.mkShell {
          packages = [
            pythonEnv
            pkgs.poetry
          ];
        };
      });
}
