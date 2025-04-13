import { Worker } from '@temporalio/worker';
// import { multiLanguageWorkflow } from '../apps/ts/workflow';
import { tsActivity } from './activities';

async function run() {
  const worker = await Worker.create({
    workflowsPath: require.resolve('./workflow'),
    activities: {
      tsActivity, // Register TypeScript activity
    },
    taskQueue: 'ts-tasks-queue',
  });

  await worker.run();
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
