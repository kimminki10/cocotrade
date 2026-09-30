import type { NextConfig } from "next";

// 브라우저는 같은 출처의 /api/*만 호출하고, 여기서 백엔드로 넘긴다.
// rewrites는 빌드 결과에 구워지므로 API_URL은 빌드 때도 넣어야 한다.
const apiUrl = process.env.API_URL ?? "http://localhost:8000";

// 원격 개발 환경의 경로 프록시(/some/prefix/...) 뒤에서 띄울 때만 쓴다. 배포에서는 비워 둔다.
const basePath = process.env.BASE_PATH || undefined;
// 개발 서버에 접근을 허용할 추가 호스트 이름 (쉼표 구분).
const allowedDevOrigins = process.env.ALLOWED_DEV_ORIGINS?.split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

const nextConfig: NextConfig = {
  output: "standalone",
  basePath,
  allowedDevOrigins,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${apiUrl}/api/:path*` }];
  },
};

export default nextConfig;
