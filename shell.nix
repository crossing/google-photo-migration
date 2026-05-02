{ pkgs ? import <nixpkgs> {} }:

let
  poetryEnv = pkgs.poetry2nix.mkPoetryEnv {
    projectDir = ./.;
    python = pkgs.python311;
    preferWheels = true;
  };
in
pkgs.mkShell {
  packages = [
    poetryEnv
    pkgs.poetry
    pkgs.google-cloud-sdk
    pkgs.sqlite
  ];

  shellHook = ''
    echo "Google Photo Migration Dev Environment (poetry2nix)"
  '';
}
