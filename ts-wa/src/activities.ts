import { Context } from '@temporalio/activity';
import { sansadSessionPipeline } from './pipeline/sansad-session-pipeline';

export async function tsActivity(inputString: string): Promise<any> {
  console.log('Running TypeScript activity with input:', inputString);
  const sansadSessionQuestions = await sansadSessionPipeline('18', 'iv');

  return sansadSessionQuestions;
}
