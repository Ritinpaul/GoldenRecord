#!/usr/bin/env node
/**
 * GoldenRecord Unified Startup Script
 * Starts PGlite, generates data, runs pipeline, and serves everything
 */
import { spawn, execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

console.log('========================================');
console.log('  GoldenRecord: Starting Platform');
console.log('========================================\n');

// Start PGlite server
console.log('[1/5] Starting PGlite PostgreSQL server...');
const pglite = spawn('node', [join(__dirname, 'database/pglite-server.mjs')], {
  stdio: 'pipe',
  detached: false,
});

let dbReady = false;

pglite.stdout.on('data', (data) => {
  const msg = data.toString().trim();
  console.log(`[PGlite] ${msg}`);
  if (msg.includes('Server listening')) {
    dbReady = true;
    startDataGeneration();
  }
});

pglite.stderr.on('data', (data) => {
  console.error(`[PGlite Error] ${data.toString().trim()}`);
});

pglite.on('close', (code) => {
  console.log(`[PGlite] exited with code ${code}`);
  process.exit(code);
});

function startDataGeneration() {
  console.log('\n[2/5] Generating synthetic data...');
  try {
    execSync('python3 pipeline/generate_synthetic_data.py', {
      cwd: __dirname,
      stdio: 'inherit',
      timeout: 120000,
    });
    startPipeline();
  } catch (e) {
    console.log('[DataGen] Failed or already has data, continuing...');
    startPipeline();
  }
}

function startPipeline() {
  console.log('\n[3/5] Running entity resolution pipeline...');
  try {
    execSync('python3 pipeline/orchestrator.py', {
      cwd: __dirname,
      stdio: 'inherit',
      timeout: 180000,
    });
  } catch (e) {
    console.log('[Pipeline] Pipeline completed with warnings or no new data');
  }
  startApiServer();
}

let apiProcess = null;

function startApiServer() {
  console.log('\n[4/5] Starting FastAPI backend...');
  apiProcess = spawn('python3', ['-m', 'uvicorn', 'api.main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'], {
    cwd: __dirname,
    stdio: 'inherit',
  });

  apiProcess.on('close', (code) => {
    console.log(`[API] exited with code ${code}`);
  });

  // Wait a moment then start frontend
  setTimeout(startFrontend, 3000);
}

function startFrontend() {
  console.log('\n[5/5] Starting React frontend...');
  const vite = spawn('npx', ['vite', 'preview', '--port', '3000', '--host'], {
    cwd: __dirname,
    stdio: 'inherit',
  });

  vite.on('close', (code) => {
    console.log(`[Frontend] exited with code ${code}`);
  });

  console.log('\n========================================');
  console.log('  GoldenRecord is running!');
  console.log('  Frontend: http://localhost:3000');
  console.log('  API:      http://localhost:8000');
  console.log('========================================');
}

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n\nShutting down GoldenRecord...');
  pglite.kill('SIGINT');
  if (apiProcess) apiProcess.kill('SIGINT');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n\nShutting down GoldenRecord...');
  pglite.kill('SIGTERM');
  if (apiProcess) apiProcess.kill('SIGTERM');
  process.exit(0);
});
