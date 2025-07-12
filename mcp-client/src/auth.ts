import * as jose from 'jose';

// --- Auth Token Generation ---
export async function createAuthToken(): Promise<string> {
  const privateKeyPem = process.env.MCP_PRIVATE_KEY;
  if (!privateKeyPem) {
    throw new Error('MCP_PRIVATE_KEY environment variable not set.');
  }

  console.log(privateKeyPem)
  const privateKey = await jose.importPKCS8(
    privateKeyPem.trim().replace(/^"""|"""$/g, ''),
    'RS256'
  );

  const jwt = await new jose.SignJWT({})
    .setProtectedHeader({ alg: 'RS256' })
    .setIssuedAt()
    .setIssuer('urn:notpatrick:client')
    .setAudience('urn:notpatrick:server')
    .setExpirationTime('2h')
    .sign(privateKey);

  return jwt;
}
