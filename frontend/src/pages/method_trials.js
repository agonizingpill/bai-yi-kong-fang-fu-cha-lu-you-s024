        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "上次实见试用批",
  "module": "估计方法试用",
  "caption": "试用批台账",
  "detail": "开批时选好房间和复访日，用同一份历史算出并锁定两种估计：现行滞后回归与试用上次实见。同房同日后来登记的实见自动为两种估计评分；满五个房日且试用法平均绝对误差更小时，复核员才可启用。两批同时提交启用，先办成的生效，另一批只留对比结果，重试也不能启用。",
  "path": "/method_trials",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "status",
      "label": "状态"
    },
    {
      "name": "scored_days",
      "label": "已评分房日"
    },
    {
      "name": "current_mae",
      "label": "现行法 MAE"
    },
    {
      "name": "trial_mae",
      "label": "试用法 MAE"
    },
    {
      "name": "token",
      "label": "后台评估凭证"
    }
  ],
  "layout": "split",
  "view": "grid",
  "actions": [
    {
      "name": "open_trial",
      "label": "开试用批",
      "path": "/method_trials/open-trial",
      "fields": [
        {
          "name": "pairs",
          "label": "房日清单（空房与复访日）",
          "kind": "json",
          "initial": [
            {
              "room_code": "ROOM-17",
              "target_day": "2090-04-05"
            }
          ]
        }
      ],
      "help": "选好房间和复访日，后台用同一份历史算出两种估计。已登记实见的复访日不能作为试用房日。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "lock_trial",
      "label": "锁定试用批",
      "path": "/method_trials/lock-trial",
      "fields": [
        {
          "name": "code",
          "label": "试用批编号",
          "kind": "text",
          "initial": "TRIAL-QA"
        },
        {
          "name": "token",
          "label": "后台评估凭证",
          "kind": "token",
          "initial": ""
        }
      ],
      "help": "历史未发生变化才锁定两种估计，批次进入试用中，等待实见评分。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "enable_trial",
      "label": "启用试用法",
      "path": "/method_trials/enable-trial",
      "fields": [
        {
          "name": "code",
          "label": "试用批编号",
          "kind": "text",
          "initial": "TRIAL-QA"
        }
      ],
      "help": "满五个已评分房日且试用法平均绝对误差更小才可启用；两批同时提交时先办成的生效，另一批只留对比结果。",
      "roles": [
        "reviewer"
      ],
      "success": "已启用"
    }
  ]
};

        export const {title} = page;
        export const key = "method_trials";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
