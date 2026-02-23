#!/usr/bin/env node

/**
 * Plan vs. Git Diff Analyzer
 * 
 * Compares planned changes against actual git changes to calculate adherence metrics.
 * Used by /system-review command for Step 1: Auto-Diff.
 * 
 * Usage: node analyze-plan-diff.js <plan-file> [feature-name]
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Parse arguments
const planFile = process.argv[2];
const featureName = process.argv[3] || 'feature';

if (!planFile) {
  console.error('Usage: node analyze-plan-diff.js <plan-file> [feature-name]');
  process.exit(1);
}

// Read plan file
const planContent = fs.readFileSync(planFile, 'utf-8');

// Extract planned files from plan
function extractPlannedFiles(plan) {
  const plannedFiles = [];
  const plannedTargets = [];
  const referencedPatterns = [];
  
  // Extract "New Files to Create" section
  const newFilesMatch = plan.match(/### New Files to Create[\s\S]*?(?=###|$)/i);
  if (newFilesMatch) {
    const fileLines = newFilesMatch[0].split('\n')
      .filter(line => line.trim().startsWith('- `') || line.trim().startsWith('- `'))
      .map(line => {
        const match = line.match(/`([^`]+)`/);
        return match ? match[1] : null;
      })
      .filter(Boolean);
    plannedFiles.push(...fileLines);
  }
  
  // Extract task targets from "STEP-BY-STEP TASKS" section
  const tasksSection = plan.match(/## STEP-BY-STEP TASKS[\s\S]*?(?=##|$)/i);
  if (tasksSection) {
    const taskHeaders = tasksSection[0].match(/### (CREATE|UPDATE|ADD|REMOVE|REFACTOR|MIRROR) (.+)/gi);
    if (taskHeaders) {
      taskHeaders.forEach(header => {
        const match = header.match(/### (?:CREATE|UPDATE|ADD|REMOVE|REFACTOR|MIRROR) (.+)/i);
        if (match && match[1]) {
          const target = match[1].trim().split(' ')[0]; // First word is file path
          plannedTargets.push(target);
          plannedFiles.push(target);
        }
      });
    }
    
    // Extract PATTERN references from tasks
    const patternRefs = tasksSection[0].match(/- \*\*PATTERN\*\*:?.*\(([^)]+)\)/gi);
    if (patternRefs) {
      patternRefs.forEach(ref => {
        const match = ref.match(/\(([^)]+)\)/);
        if (match) {
          referencedPatterns.push(match[1]);
        }
      });
    }
  }
  
  // Extract "Relevant Codebase Files" section
  const relevantFilesMatch = plan.match(/### Relevant Codebase Files[\s\S]*?(?=###|$)/i);
  if (relevantFilesMatch) {
    const fileLines = relevantFilesMatch[0].split('\n')
      .filter(line => line.trim().startsWith('- `'))
      .map(line => {
        const match = line.match(/`([^`]+)`/);
        return match ? match[1] : null;
      })
      .filter(Boolean);
    plannedFiles.push(...fileLines);
  }
  
  return {
    plannedFiles: [...new Set(plannedFiles)],
    plannedTargets: [...new Set(plannedTargets)],
    referencedPatterns: [...new Set(referencedPatterns)]
  };
}

// Get actual git changes
function getActualChanges() {
  try {
    // Try to get staged changes first
    let diffOutput;
    try {
      diffOutput = execSync('git diff --cached --name-only', { encoding: 'utf-8' });
    } catch {
      // If no staged changes, get recent commits
      try {
        diffOutput = execSync('git diff HEAD~1 HEAD --name-only', { encoding: 'utf-8' });
      } catch {
        // If no commits, get unstaged changes
        diffOutput = execSync('git diff --name-only', { encoding: 'utf-8' });
      }
    }
    
    const actualFiles = diffOutput.split('\n').filter(line => line.trim());
    
    // Get detailed diff for pattern analysis
    let detailedDiff = '';
    try {
      detailedDiff = execSync('git diff --cached', { encoding: 'utf-8' });
    } catch {
      try {
        detailedDiff = execSync('git diff HEAD~1 HEAD', { encoding: 'utf-8' });
      } catch {
        detailedDiff = execSync('git diff', { encoding: 'utf-8' });
      }
    }
    
    return { actualFiles, detailedDiff };
  } catch (error) {
    console.error('Warning: Could not get git changes:', error.message);
    return { actualFiles: [], detailedDiff: '' };
  }
}

// Calculate adherence metrics
function calculateMetrics(planned, actual) {
  const plannedSet = new Set(planned.plannedFiles);
  const actualSet = new Set(actual.actualFiles);
  
  // File adherence
  const overlap = [...plannedSet].filter(file => actualSet.has(file));
  const fileAdherence = plannedSet.size > 0 
    ? (overlap.length / plannedSet.size) * 100 
    : 100;
  
  // Scope creep (files changed but not in plan)
  const scopeCreep = [...actualSet].filter(file => !plannedSet.has(file));
  
  // Missing files (in plan but not changed)
  const missingFiles = [...plannedSet].filter(file => !actualSet.has(file));
  
  // Pattern compliance (check if referenced patterns appear in diff)
  let patternCompliance = 100;
  if (planned.referencedPatterns.length > 0) {
    const patternsFound = planned.referencedPatterns.filter(pattern => 
      actual.detailedDiff.includes(pattern.split(':')[0]) // Check if file is in diff
    );
    patternCompliance = (patternsFound.length / planned.referencedPatterns.length) * 100;
  }
  
  return {
    fileAdherence: Math.round(fileAdherence * 10) / 10,
    patternCompliance: Math.round(patternCompliance * 10) / 10,
    scopeCreep,
    missingFiles,
    overlap,
    totalPlanned: planned.plannedFiles.length,
    totalActual: actual.actualFiles.length
  };
}

// Generate report
function generateReport(metrics, planned) {
  const planAdherenceScore = metrics.fileAdherence; // Simplified - task completion from execution report
  
  console.log('## Auto-Diff Analysis\n');
  console.log('```');
  console.log(`Planned Files: ${metrics.totalPlanned}`);
  console.log(`Actual Files:  ${metrics.totalActual}`);
  console.log(`Overlap:       ${metrics.overlap.length}`);
  console.log('');
  console.log(`File Adherence:    ${metrics.fileAdherence}% (${metrics.overlap.length}/${metrics.totalPlanned} planned files were modified)`);
  console.log(`Pattern Compliance: ${metrics.patternCompliance}% (${planned.referencedPatterns.length} patterns referenced)`);
  console.log(`Scope Creep:       ${metrics.scopeCreep.length > 0 ? '+' + metrics.scopeCreep.length : '0'} files (not in plan)`);
  console.log('');
  console.log(`Plan Adherence Score: ${Math.round(planAdherenceScore * 10) / 10}%`);
  console.log('```');
  
  if (metrics.scopeCreep.length > 0) {
    console.log('\n**Files modified but not in plan:**\n');
    metrics.scopeCreep.forEach(file => {
      console.log(`- \`${file}\``);
    });
  }
  
  if (metrics.missingFiles.length > 0) {
    console.log('\n**Files in plan but not modified:**\n');
    metrics.missingFiles.forEach(file => {
      console.log(`- \`${file}\``);
    });
  }
}

// Main execution
const planned = extractPlannedFiles(planContent);
const actual = getActualChanges();
const metrics = calculateMetrics(planned, actual);

generateReport(metrics, planned);

// Output JSON for further processing
if (process.argv.includes('--json')) {
  console.log('\n\n## JSON Output\n```json');
  console.log(JSON.stringify(metrics, null, 2));
  console.log('```');
}
