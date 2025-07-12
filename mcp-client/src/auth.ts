import * as jose from 'jose';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// --- Auth Token Generation ---
export async function createAuthToken(): Promise<string> {
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  const privateKeyPath = path.resolve(__dirname, '../private_key.pem');

  if (!fs.existsSync(privateKeyPath)) {
    throw new Error(
      `Private key not found at ${privateKeyPath}. Please copy it to the 'mcp-client/' directory.`
    );
  }

  const privateKeyPem = fs.readFileSync(privateKeyPath, 'utf-8');

  const privateKey = await jose.importPKCS8(privateKeyPem, 'RS256');

  const jwt = await new jose.SignJWT({})
    .setProtectedHeader({ alg: 'RS256' })
    .setIssuedAt()
    .setIssuer('urn:notpatrick:client')
    .setAudience('urn:notpatrick:server')
    .setExpirationTime('1m')
    .sign(privateKey);

  return jwt;
}
