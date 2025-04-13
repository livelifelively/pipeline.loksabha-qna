import path from 'path';
import fs from 'fs';
import { groupBy } from 'lodash';

import { ProgressIteration, StepStatus } from '../pipeline/pipeline';
import { findProjectRoot, kebabCaseNames, filenameGenerator } from '../utils/project-root';
import { downloadPDFs } from '../utils/fetch-pdf-from-url';
import { successfulStepDataFilePath } from '../utils/pipeline-utils';
import { ParliamentQuestion } from '.';

export async function fetchMetaAnalysisForQuestionsPdfs(outputs: Record<string, any>): Promise<any> {
  const { downloadedSansadSessionQuestions } = outputs;

  // const sansadSessionDirectory = path.join(__dirname, `../../../sansad/${sansad}/${session}`);
  // const fetchedQnAPdfProgressStatusFilePath = path.join(
  //   sansadSessionDirectory,
  //   'sansad-session-pipeline-logs/progress-status.json'
  // );
  // const fetchedQnAPdfProgressStatus = require(fetchedQnAPdfProgressStatusFilePath);

  // console.log(JSON.stringify(fetchedQnAPdfProgressStatus));

  // const fetchedQnAPdfDataFilePath = successfulStepDataFilePath(fetchedQnAPdfProgressStatus, 1);

  // if (!fetchedQnAPdfDataFilePath) {
  //   throw new Error("Step's Successfull status data file not found");
  // }

  // const absolutePath = path.join(findProjectRoot(), fetchedQnAPdfDataFilePath);
  // const fetchedQnAPdfData = require(absolutePath);

  // let baseData = fetchedQnAPdfData.data.downloadedSansadSessionQuestions.map(
  const baseData = downloadedSansadSessionQuestions.map((val: ParliamentQuestion): ParliamentQuestion => {
    return {
      questionNumber: val.questionNumber,
      subjects: val.subjects.trim(),
      loksabhaNumber: val.loksabhaNumber.trim(),
      member: val.member.map((m) => m.trim()),
      ministry: val.ministry.trim(),
      type: val.type,
      date: val.date.trim(),
      questionsFilePathLocal: val.questionsFilePathLocal.trim(),
      questionsFilePathWeb: val.questionsFilePathWeb.trim(),
      questionsFilePathHindiLocal: val.questionsFilePathHindiLocal?.trim(),
      questionsFilePathHindiWeb: val.questionsFilePathHindiWeb?.trim(),
      questionText: val.questionText?.trim(),
      answerText: val.answerText?.trim(),
      sessionNo: val.sessionNo?.trim(),
    };
  });

  console.log(JSON.stringify(baseData));

  return {
    status: 'SUCCESS',
    cleanedQuestionAnswerData: baseData,
  };

  // #TODO
  // number of pages
  // has table
  // number of characters in the answer
  // question text
  // answer text
  // structure conformance

  // input question
  // output meta analysis on the document

  // used to filter questions -
  // 1. those with tables = high priority
  // 2. fewer answer characters or fewer pages = low priority
}
