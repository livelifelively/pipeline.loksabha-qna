import * as wf from '@temporalio/workflow';

const { proxyActivities } = wf;

const activities = proxyActivities({
  startToCloseTimeout: '600000 second',
  taskQueue: 'ts-tasks-queue',
});

const pythonActivities = proxyActivities({
  startToCloseTimeout: '600000 second',
  taskQueue: 'py-tasks-queue',
});

export async function multiLanguageWorkflow(initialString: string): Promise<string> {
  const tsResult = await activities.tsActivity(initialString);
  return 'Hello World';
}
