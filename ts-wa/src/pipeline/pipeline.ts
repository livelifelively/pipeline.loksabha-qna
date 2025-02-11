import path from 'path';
import fs from 'fs';
import { keyBy, map, size } from 'lodash';

import { findProjectRoot } from '../file-utils/project-root';

export interface PipelineStep {
  name: string;
  function: any;
  input: any;
  output?: any;
  status?: 'SUCCESS' | 'FAILURE' | 'PARTIAL';
  error?: any;
  key: string;
}

interface PipelineConfig {
  steps: PipelineStep[];
  initialOutputs: Record<string, any>;
  progressDir: string;
  progressFile: string;
}

// Define the necessary interfaces
interface ProgressIteration {
  iteration: number;
  lastIteration?: number;
  timeStamp: Date;
  steps: ProgressStep[];
}

interface ProgressStep {
  step: number;
  logFile: string;
  status: 'SUCCESS' | 'FAILURE' | 'PARTIAL';
}

interface ProgressData {
  message: string;
  data: any;
  error?: any;
  key: string;
  timeStamp?: Date;
}

function initializeDirectories(progressDir: string, progressFile: string): void {
  fs.mkdirSync(progressDir, { recursive: true });
  if (!fs.existsSync(progressFile)) {
    fs.writeFileSync(progressFile, JSON.stringify([]));
  }
}

function createNewIteration(progressFile: string): ProgressIteration {
  const projectRoot = findProjectRoot();
  const filePath = path.join(projectRoot, progressFile);

  const progressStatus: ProgressIteration[] = JSON.parse(fs.readFileSync(progressFile, 'utf8'));
  return {
    iteration: progressStatus.length + 1,
    timeStamp: new Date(),
    steps: [],
  };
}

function getLastIteration(progressFile: string): ProgressIteration {
  const progressStatus: ProgressIteration[] = JSON.parse(fs.readFileSync(progressFile, 'utf8'));
  return progressStatus[progressStatus.length - 1];
}

async function logProgress(
  progressDir: string,
  progressFile: string,
  progressData: ProgressData,
  status: 'SUCCESS' | 'FAILURE' | 'PARTIAL',
  iteration: ProgressIteration
): Promise<void> {
  const progressStatus: ProgressIteration[] = JSON.parse(fs.readFileSync(progressFile, 'utf8'));
  const progressDataLogFile = path.join(progressDir, `${iteration.iteration}.${progressData.key}.log.json`);
  const projectRoot = await findProjectRoot();

  const relativeLogFile = path.relative(projectRoot, progressDataLogFile);

  iteration.steps.push({
    step: iteration.steps.length,
    logFile: relativeLogFile,
    status,
  });

  let existingLogs: ProgressData;
  if (fs.existsSync(progressDataLogFile)) {
    existingLogs = JSON.parse(fs.readFileSync(progressDataLogFile, 'utf8'));
  }

  existingLogs = { ...progressData, timeStamp: new Date() };
  fs.writeFileSync(progressDataLogFile, JSON.stringify(existingLogs, null, 2));

  const existingIterationIndex = progressStatus.findIndex((iter) => iter.iteration === iteration.iteration);
  if (existingIterationIndex !== -1) {
    progressStatus[existingIterationIndex] = iteration;
  } else {
    progressStatus.push(iteration);
  }

  fs.writeFileSync(progressFile, JSON.stringify(progressStatus, null, 2));
}

// Modified orchestration function to return the last executed step output or previously saved result if all steps were successful
async function orchestrationFunction(
  outputs: Record<string, any>,
  steps: PipelineStep[],
  resumeFromLastSuccessful: boolean
): Promise<any> {
  const previousIteration = getLastIteration(outputs.progressFile);

  // Check if the previous iteration was completely successful
  if (
    resumeFromLastSuccessful &&
    previousIteration &&
    previousIteration.steps.length === steps.length &&
    previousIteration.steps.every((step) => step.status === 'SUCCESS')
  ) {
    console.log('All steps were previously completed successfully. Returning the last step output.');
    const lastStep = previousIteration.steps[previousIteration.steps.length - 1];
    const lastStepOutput = JSON.parse(fs.readFileSync(lastStep.logFile, 'utf8'));
    return lastStepOutput.data;
  }

  const currentIteration = createNewIteration(outputs.progressFile);

  if (
    previousIteration &&
    (steps.length !== previousIteration.steps.length || previousIteration.steps[steps.length - 1].status !== 'SUCCESS')
  ) {
    for (let s in previousIteration.steps) {
      if (previousIteration.steps[s].status === 'SUCCESS') {
        currentIteration.steps[s] = { ...previousIteration.steps[s] };
        let stepOutput: any = await fs.readFileSync(previousIteration.steps[s].logFile, 'utf8');
        stepOutput = JSON.parse(stepOutput);
        outputs = { ...outputs, ...stepOutput.data };
      } else {
        break;
      }
    }
  }

  let lastStepOutput = null;

  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    const progressStep = currentIteration.steps.find((s) => s.step === i);

    if (progressStep && progressStep.status === 'SUCCESS') {
      console.log(`Step ${i} (${step.name}) already completed successfully.`);
      outputs = { ...outputs, ...step.output };
      lastStepOutput = step.output;
      continue;
    }

    try {
      console.log(`Executing step ${i} (${step.name})...`);
      const { status, ...stepOutputs } = await step.function(outputs);

      step.status = status;
      step.output = stepOutputs;
      outputs = { ...outputs, ...stepOutputs };
      lastStepOutput = stepOutputs;

      if (step.status !== 'SUCCESS') {
        throw new Error();
      }

      await logProgress(
        outputs.progressDir,
        outputs.progressFile,
        {
          message: `Step ${i} (${step.name}) completed successfully.`,
          data: step.output,
          key: `STEP_${i}_${step.status}_${step.name}`,
        },
        'SUCCESS',
        currentIteration
      );
    } catch (error: any) {
      step.status = step.status || 'FAILURE';
      await logProgress(
        outputs.progressDir,
        outputs.progressFile,
        {
          message: `Step ${i} (${step.name}) failed.`,
          data: { ...step.output },
          error: step.status !== 'PARTIAL' ? { error: [error.message, step.error] } : {},
          key: `STEP_${i}_${step.status}_${step.name}`,
        },
        step.status,
        currentIteration
      );

      console.error(`Step ${i} (${step.name}) failed. Manual intervention required.`);
      throw new Error(`Step ${i} (${step.name}) failed. Manual intervention required.`);
    }

    const progressStatus: ProgressIteration[] = JSON.parse(fs.readFileSync(outputs.progressFile, 'utf8'));
    const existingIterationIndex = progressStatus.findIndex((iter) => iter.iteration === currentIteration.iteration);
    if (existingIterationIndex !== -1) {
      progressStatus[existingIterationIndex] = currentIteration;
    } else {
      progressStatus.push(currentIteration);
    }
    fs.writeFileSync(outputs.progressFile, JSON.stringify(progressStatus, null, 2));
  }

  return lastStepOutput;
}

// New function to call the orchestration function with configuration and return the last executed step output
export async function runPipeline(
  steps: PipelineStep[],
  initialOutputs: any,
  progressDir: any,
  progressFile: any,
  resumeFromLastSuccessful: boolean = true
): Promise<any> {
  initializeDirectories(progressDir, progressFile);

  try {
    const lastStepOutput = await orchestrationFunction(
      { ...initialOutputs, progressDir, progressFile },
      steps,
      resumeFromLastSuccessful
    );
    return lastStepOutput;
  } catch (error) {
    console.error('Error in processing: ', error);
    throw error;
  }
}
