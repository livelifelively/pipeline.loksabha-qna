import path from 'path';

import { PipelineStep } from './pipeline';
import { runPipeline } from './pipeline';
import { fetchAndCategorizeQuestionsPdfs } from '../parliament-questions';
import { fetchMetaAnalysisForQuestionsPdfs } from '../parliament-questions/questions-meta-analysis';

export async function sansadSessionPipeline(sansad: string, session: string): Promise<any> {
  console.log('SANSAD SESSION PROCESSING INITIALIZED: ', sansad, session);

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
    {
      name: 'Fetch Meta Analysis for Questions PDFs',
      function: fetchMetaAnalysisForQuestionsPdfs,
      key: 'FETCH_META_ANALYSIS_FOR_QUESTIONS_PDFS',
      input: {
        sansad: sansad,
        session: session,
        downloadedSansadSessionQuestions: [],
      },
    },
  ];

  let outputs: Record<string, any> = {
    sansad: sansad,
    session: session,
    failedSansadSessionQuestionDownload: [],
    downloadedSansadSessionQuestions: [],
    cleanedQnAData: [],
  };

  const sansadSessionDirectory = path.join(__dirname, `../../../sansad-${sansad}/${session}`);
  const sansadProgressDir = path.join(sansadSessionDirectory, 'sansad-session-pipeline-logs');
  const progressStatusFile = path.join(sansadProgressDir, 'progress-status.json');

  try {
    const lastStepOutput = await runPipeline(steps, outputs, sansadProgressDir, progressStatusFile);
    return lastStepOutput;
  } catch (error) {
    console.error('Error in processing: ', error);
  }
}
