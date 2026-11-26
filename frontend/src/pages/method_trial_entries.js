        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "试用房日评分",
  "module": "估计方法试用",
  "caption": "试用房日台账",
  "detail": "每个试用房日在锁批时固化的两种估计，以及同房同日后来登记的实见评分。落选批次在此只保留对比结果。",
  "path": "/method_trial_entries",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "batch_code",
      "label": "试用批"
    },
    {
      "name": "room_code",
      "label": "空房"
    },
    {
      "name": "target_day",
      "label": "复访日"
    },
    {
      "name": "current_estimate",
      "label": "现行法估计"
    },
    {
      "name": "trial_estimate",
      "label": "试用法估计"
    },
    {
      "name": "actual_count",
      "label": "实见数"
    },
    {
      "name": "current_error",
      "label": "现行法误差"
    },
    {
      "name": "trial_error",
      "label": "试用法误差"
    }
  ],
  "layout": "stack",
  "view": "table",
  "actions": []
};

        export const {title} = page;
        export const key = "method_trial_entries";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
