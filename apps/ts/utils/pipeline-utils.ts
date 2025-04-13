import { ProgressIteration } from '../pipeline/pipeline';

export function successfulStepDataFilePath(fetchedQnAPdfProgressStatus: ProgressIteration[], stepNumber: number) {
  const successfulStepIterations = fetchedQnAPdfProgressStatus.find((iteration: ProgressIteration) => {
    return iteration.steps[stepNumber - 1].status === 'SUCCESS';
  });

  return successfulStepIterations?.steps[stepNumber - 1]?.logFile;
}
