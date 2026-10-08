{
  description = "Môi trường phát triển Web App Quản Lý Xưởng Gỗ";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forEachSupportedSystem = f: nixpkgs.lib.genAttrs supportedSystems (system: f {
        pkgs = import nixpkgs { inherit system; };
      });
    in
    {
      devShells = forEachSupportedSystem ({ pkgs }: {
        default = pkgs.mkShell {
          packages = with pkgs; [
            (python3.withPackages (ps: with ps; [
              fastapi
              uvicorn
              sqlalchemy
              jinja2
              python-multipart
              bcrypt
              itsdangerous
              openpyxl
              pytest
              httpx
              aiofiles
            ]))
            sqlite
          ];

          shellHook = ''
            echo "🌿 Môi trường Quản Lý Xưởng Gỗ đã sẵn sàng!"
            echo "Python: $(python3 --version)"
          '';
        };
      });
    };
}
