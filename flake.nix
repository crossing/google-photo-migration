{
  description = "Google Photos Migration Tool";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
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

        pythonApp = mkPoetryApplication {
          projectDir = ./.;
        };

        pythonEnv = mkPoetryEnv {
          projectDir = ./.;
        };
      in
      {
        packages.default = pythonApp;

        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.poetry
          ];
        };
      });
}
