import { Worker } from '@temporalio/worker';
import { tsActivity } from './activities';

async function run() {
  const worker = await Worker.create({
    workflowsPath: require.resolve('./multi-language.workflow'),
    activities: {
      tsActivity,
    },
    taskQueue: 'ts-tasks-queue',
  });

  await worker.run();
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
