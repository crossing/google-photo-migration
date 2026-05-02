{
  description = "Google Photos Migration Tool";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ poetry2nix.overlays.default ];
        };
        p2n = pkgs.poetry2nix;
      in
      {
        packages.default = p2n.mkPoetryApplication {
          projectDir = ./.;
          preferWheels = true;
        };

        devShells.default = pkgs.mkShell {
          packages = [
            (p2n.mkPoetryEnv {
              projectDir = ./.;
              preferWheels = true;
            })
            pkgs.poetry
          ];
        };
      });
}
