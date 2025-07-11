import { openai } from '@ai-sdk/openai';
import { generateText, experimental_createMCPClient as createMCPClient } from 'ai';
import { z } from 'zod';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function main() {
  console.log('🤖 Starting MCP client test...');

  // Create MCP client connected to our FastMCP server
  const mcpClient = await createMCPClient({
    transport: {
      type: 'sse',
      url: 'http://localhost:8000/sse',
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
