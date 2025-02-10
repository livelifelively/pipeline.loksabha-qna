import { Context } from '@temporalio/activity';

export async function tsActivity(inputString: string): Promise<string> {
  console.log("Running TypeScript activity with input:", inputString);
  return `TS: ${inputString}`;
}