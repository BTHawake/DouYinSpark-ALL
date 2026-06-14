const { createApp, ref, reactive, computed } = Vue;
const app = createApp({
  setup() {
    const match_mode_options = [
      { id: "nickname", label: "昵称", value: "nickname" },
      { id: "short_id", label: "抖音号", value: "short_id" },
    ];

    const log_level_options = [
      { id: "Debug", label: "Debug", value: "Debug" },
      { id: "Info", label: "Info", value: "Info" },
      { id: "Warning", label: "Warning", value: "Warning" },
      { id: "Error", label: "Error", value: "Error" },
    ];

    const group_match_mode_options = [
      { id: "name", label: "群名称", value: "name" },
      { id: "id", label: "群ID", value: "id" },
    ];

    const form = reactive({
      MESSAGE_TEMPLATE:
        "[API]",
      HITOKOTO_TYPES: ["文学", "影视", "诗词", "哲学"],
      MATCH_MODE: "short_id",
      GROUP_MATCH_MODE: "name",
      BROWSER_TIMEOUT: 120000,
      FRIEND_LIST_WAIT_TIME: 2000,
      TASK_RETRY_TIMES: 3,
      LOG_LEVEL: "Info",
      ACCOUNTS: [
        {
          username: "user1",
          unique_id: "12345678905",
          cookies: "cookie1",
          targets: ["friend1", "friend2"],
          groups: [],
        },
      ],
    });

    const configJSON = computed(() => {
      return JSON.stringify(
        {
          messageTemplate: form.MESSAGE_TEMPLATE,
          hitokotoTypes: form.HITOKOTO_TYPES,
          matchMode: form.MATCH_MODE,
          groupMatchMode: form.GROUP_MATCH_MODE,
          browserTimeout: form.BROWSER_TIMEOUT,
          friendListTimeout: form.FRIEND_LIST_WAIT_TIME,
          taskRetryTimes: form.TASK_RETRY_TIMES,
          logLevel: form.LOG_LEVEL,
          accounts: form.ACCOUNTS.map((account) => {
            let cookiesVal = account.cookies;
            if (typeof cookiesVal === "string" && cookiesVal.trim()) {
              try { cookiesVal = JSON.parse(cookiesVal); } catch (e) {}
            }
            return {
              username: account.username,
              unique_id: account.unique_id,
              cookies: cookiesVal,
              targets: account.targets,
              groups: account.groups || [],
            };
          }),
        },
        null,
        2
      );
    });

    const copyConfig = () => {
      navigator.clipboard.writeText(configJSON.value).then(
        () => ElementPlus.ElMessage.success("CONFIG 已复制到剪贴板"),
        (err) => ElementPlus.ElMessage.error("复制失败: " + err)
      );
    };

    const addAccount = () => {
      form.ACCOUNTS.push({
        username: "",
        unique_id: "",
        cookies: "",
        targets: [],
        groups: [],
      });
    };

    const removeAccount = (index) => {
      form.ACCOUNTS.splice(index, 1);
    };

    return {
      match_mode_options,
      group_match_mode_options,
      log_level_options,
      form,
      configJSON,
      copyConfig,
      addAccount,
      removeAccount,
    };
  },
});
app.use(ElementPlus);
app.mount("#app");
