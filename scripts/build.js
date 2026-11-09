// Builds the Docker image tagged with both "latest" and the version from package.json.
// Usage: node scripts/build.js [extra docker build args, e.g. --no-cache]
const { spawnSync } = require("node:child_process");
const { name, version } = require("../package.json");

const args = [
  "build",
  "-t", `${name}:latest`,
  "-t", `${name}:${version}`,
  ...process.argv.slice(2),
  ".",
];

console.log(`docker ${args.join(" ")}`);
const result = spawnSync("docker", args, { stdio: "inherit" });
process.exit(result.status ?? 1);
