import path from 'path';

import { PipelineStep } from './pipeline';
import { runPipeline } from './pipeline';
import { fetchAndCategorizeQuestionsPdfs } from '../parliament-questions';

export async function sansadSessionQuestionsPipeline(sansad: string, session: string): Promise<any> {
  console.log('SANSAD SESSION QUESTIONS PROCESSING INITIALIZED: ', sansad, session);

  const steps: PipelineStep[] = [
    {
      name: 'Fetch Questions PDFs',
      function: fetchAndCategorizeQuestionsPdfs,
      key: 'FETCH_QUESTIONS_PDFS',
      input: {
        sansad: sansad,
        session: session,
      },
    },
  ];

  let outputs: Record<string, any> = {
    sansad: sansad,
    session: session,
    failedSansadSessionQuestionDownload: [],
    downloadedSansadSessionQuestions: [],
  };

  const sansadSessionDirectory = path.join(__dirname, `../../../sansad/${sansad}/${session}`);
  const sansadProgressDir = path.join(sansadSessionDirectory, 'sansad-session-pipeline-logs');
  const progressStatusFile = path.join(sansadProgressDir, 'progress-status.json');

  try {
    const lastStepOutput = await runPipeline(steps, outputs, sansadProgressDir, progressStatusFile);
    return lastStepOutput;
  } catch (error) {
    console.error('Error in processing: ', error);
  }
}
