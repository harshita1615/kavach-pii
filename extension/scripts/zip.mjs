// Package dist/ as kavach-extension-<version>.zip for the Chrome Web Store.
//
//   npm run package
//
// A minimal ZIP writer (deflate + CRC-32 from node:zlib), so no extra dependency.

import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { crc32, deflateRawSync } from "node:zlib";

const root = new URL("../", import.meta.url);
const dist = new URL("dist/", root);
const { version } = JSON.parse(readFileSync(new URL("manifest.json", dist), "utf-8"));

function walk(dir, prefix = "") {
  return readdirSync(dir).sort().flatMap((name) => {
    const url = new URL(name, dir);
    return statSync(url).isDirectory()
      ? walk(new URL(`${name}/`, dir), `${prefix}${name}/`)
      : [{ path: `${prefix}${name}`, url }];
  });
}

const local = [];
const central = [];
let offset = 0;
// Fixed timestamp (1980-01-01) so the same build gives the same zip.
const DOS_TIME = 0;
const DOS_DATE = (0 << 9) | (1 << 5) | 1;

for (const file of walk(dist)) {
  const data = readFileSync(file.url);
  const compressed = deflateRawSync(data, { level: 9 });
  const name = Buffer.from(file.path, "utf-8");
  const crc = crc32(data);

  const header = Buffer.alloc(30);
  header.writeUInt32LE(0x04034b50, 0);
  header.writeUInt16LE(20, 4); // version needed
  header.writeUInt16LE(0x0800, 6); // UTF-8 names
  header.writeUInt16LE(8, 8); // deflate
  header.writeUInt16LE(DOS_TIME, 10);
  header.writeUInt16LE(DOS_DATE, 12);
  header.writeUInt32LE(crc, 14);
  header.writeUInt32LE(compressed.length, 18);
  header.writeUInt32LE(data.length, 22);
  header.writeUInt16LE(name.length, 26);
  local.push(header, name, compressed);

  const entry = Buffer.alloc(46);
  entry.writeUInt32LE(0x02014b50, 0);
  entry.writeUInt16LE(20, 4);
  entry.writeUInt16LE(20, 6);
  entry.writeUInt16LE(0x0800, 8);
  entry.writeUInt16LE(8, 10);
  entry.writeUInt16LE(DOS_TIME, 12);
  entry.writeUInt16LE(DOS_DATE, 14);
  entry.writeUInt32LE(crc, 16);
  entry.writeUInt32LE(compressed.length, 20);
  entry.writeUInt32LE(data.length, 24);
  entry.writeUInt16LE(name.length, 28);
  entry.writeUInt32LE(offset, 42);
  central.push(entry, name);

  offset += header.length + name.length + compressed.length;
}

const centralSize = central.reduce((n, b) => n + b.length, 0);
const end = Buffer.alloc(22);
end.writeUInt32LE(0x06054b50, 0);
end.writeUInt16LE(central.length / 2, 8);
end.writeUInt16LE(central.length / 2, 10);
end.writeUInt32LE(centralSize, 12);
end.writeUInt32LE(offset, 16);

const out = new URL(`kavach-extension-${version}.zip`, root);
writeFileSync(out, Buffer.concat([...local, ...central, end]));
console.log(`wrote kavach-extension-${version}.zip (${central.length / 2} files)`);
