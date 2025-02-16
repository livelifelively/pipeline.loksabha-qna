import path from 'path';

import { PipelineStep } from './pipeline';
import { runPipeline } from './pipeline';
import { fetchAndCategorizeQuestionsPdfs } from '../parliament-questions';
import { fetchMetaAnalysisForQuestionsPdfs } from '../parliament-questions/questions-meta-analysis';
import { adaptSourceQuestionsListToParliamentQuestions } from '../parliament-questions/adapt-input-data';

export async function sansadSessionPipeline(sansad: string, session: string): Promise<any> {
  console.log('SANSAD SESSION PROCESSING INITIALIZED: ', sansad, session);

  const steps: PipelineStep[] = [
    {
      name: 'Adapt Input Data',
      function: adaptSourceQuestionsListToParliamentQuestions,
      key: 'ADAPT_INPUT_DATA',
    },
    {
      name: 'Fetch Questions PDFs',
      function: fetchAndCategorizeQuestionsPdfs,
      key: 'FETCH_QUESTIONS_PDFS',
    },
    {
      name: 'Fetch Meta Analysis for Questions PDFs',
      function: fetchMetaAnalysisForQuestionsPdfs,
      key: 'FETCH_META_ANALYSIS_FOR_QUESTIONS_PDFS',
    },
  ];

  let outputs: Record<string, any> = {
    sansad: sansad,
    session: session,
    parliamentSessionQuestions: [],
    failedSansadSessionQuestionDownload: [],
    downloadedSansadSessionQuestions: [],
    cleanedQuestionAnswerData: [],
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
