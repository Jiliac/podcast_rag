import { openai } from '@ai-sdk/openai';
import { generateText, experimental_createMCPClient as createMCPClient } from 'ai';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import { createAuthToken } from './auth';

// --- Environment Loading ---
// Point to the root .env file for unified configuration
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, '../../.env') });


async function main() {
  console.log('🤖 Starting MCP client test...');

  // Generate JWT for authentication
  const authToken = await createAuthToken();

  // Create MCP client connected to our FastMCP server
  const mcpClient = await createMCPClient({
    transport: {
      type: 'sse',
      // url: 'http://localhost:8000/sse',
      url: 'https://notpatrick-rag-mcp.fly.dev/sse/',
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    },
  });

  console.log('✅ Connected to MCP server');

  try {
    // Get tools from the MCP server with schema discovery
    const tools = await mcpClient.tools();

    console.log('🔧 Available tools:', Object.keys(tools));

    // Test the query_podcast tool
    const result = await generateText({
      model: openai('gpt-4o'),
      prompt: `You are helping a user query the "Not Patrick" podcast content. 
      
Use the query_podcast tool to answer this question: "Quelle est l'opinion de Patrick sur le Fairphone ?"

After getting the tool result, provide a complete response that includes:
- The main information from the tool
- Any additional context or nuances
- A clear, well-structured answer

Make sure to use the tool result as your primary source of information.`,
      tools,
    });

    console.log('🎉 AI Response:');
    console.log(result.text);

    if (result.toolResults && result.toolResults.length > 0) {
      console.log('\n📋 Tool Results:');
      result.toolResults.forEach((toolResult, index) => {
        console.log(`${index + 1}: ${toolResult.toolName}:`, toolResult.result);
      });
    }

    // Test the get_episode_info tool
    console.log('\n🔍 Testing get_episode_info tool...');
    const episodeInfoResult = await generateText({
      model: openai('gpt-4o'),
      prompt: `Use the get_episode_info tool to get information about the episode from 2025-07-08. 
      
After getting the tool result, provide a summary that includes:
- The episode title
- A brief description
- The episode link
- Any other interesting metadata

Format the response nicely for the user.`,
      tools,
    });

    console.log('📺 Episode Info Response:');
    console.log(episodeInfoResult.text);

    if (episodeInfoResult.toolResults && episodeInfoResult.toolResults.length > 0) {
      console.log('\n📋 Episode Info Tool Results:');
      episodeInfoResult.toolResults.forEach((toolResult, index) => {
        console.log(`${index + 1}: ${toolResult.toolName}:`, toolResult.result);
      });
    }

  } catch (error) {
    console.error('❌ Error:', error);
  } finally {
    // Always close the MCP client
    await mcpClient.close();
    console.log('🔒 MCP client closed');
  }
}

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Run the main function
main().catch(console.error);
