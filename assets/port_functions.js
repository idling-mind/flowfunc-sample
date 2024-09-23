window.dash_clientside = Object.assign({}, window.dash_clientside, {
  flowfunc: {
    increasing_ports: function (ports, inputData, connections, context) {
      const arr = [];
      connection_count = Object.keys(connections.inputs).length;
      for (let i = 0; i <= connection_count; i++) {
        arr.push(ports.object({ name: `port${i}`, label: `object ${i}` }));
      }
      return arr;
    },
    dynamic_ports: function (ports, inputData, connections, context) {
      // Example from flume.dev
      const template =
        (inputData &&
          inputData.template &&
          Object.values(inputData.template)[0]) || // Since the control name could be anything, we just take the first value
        "";
      const re = /\{(.*?)\}/g;
      let res,
        ids = [];
      while ((res = re.exec(template)) !== null) {
        if (!ids.includes(res[1])) ids.push(res[1]);
      }
      return [
        ports.str({ name: "template", label: "Template", hidePort: true }),
        ...ids.map((id) => ports.str({ name: id, label: id })),
      ];
    },
  },
});
