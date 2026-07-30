const assert = require("node:assert/strict");
const fs = require("node:fs");

const binary = process.env.BINARY_NAME;
const repository = process.env.REPOSITORY;
assert.ok(binary, "BINARY_NAME is required");
assert.ok(repository, "REPOSITORY is required");

const installer = fs.readFileSync("scripts/install.sh", "utf8");
const release = fs.readFileSync(".github/workflows/release.yml", "utf8");
const asset = `${binary}-linux-x86_64.tar.gz`;

assert.match(installer, /Linux/);
assert.match(installer, /x86_64/);
assert.ok(installer.includes("sha256sum --check"));
assert.ok(release.includes(asset), `release workflow must create ${asset}`);
assert.ok(release.includes(`${asset}.sha256`), "release workflow must create checksum");
assert.ok(!installer.includes("github.com/jmagar/"), "legacy owner redirect is forbidden");
assert.ok(
  installer.includes(`dinglebear-ai/${repository}`),
  "installer must use the canonical repository",
);
