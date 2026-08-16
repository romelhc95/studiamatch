const blocked = (api) => {
  throw new Error(`NETWORK_EGRESS_BLOCKED:${api}`);
};

globalThis.fetch = async () => blocked("fetch");

const modules = await Promise.all([
  import("node:dns"),
  import("node:http"),
  import("node:https"),
  import("node:net"),
  import("node:tls"),
]);

const [dns, http, https, net, tls] = modules.map((module) => module.default);

for (const name of ["lookup", "resolve", "resolve4", "resolve6"]) {
  if (typeof dns[name] === "function") {
    dns[name] = () => blocked(`dns.${name}`);
  }
}

for (const module of [http, https]) {
  for (const name of ["get", "request"]) {
    if (typeof module[name] === "function") {
      module[name] = () => blocked(`${module === http ? "http" : "https"}.${name}`);
    }
  }
}

if (typeof net.Socket?.prototype?.connect === "function") {
  net.Socket.prototype.connect = () => blocked("net.Socket.connect");
}

if (typeof net.connect === "function") {
  net.connect = () => blocked("net.connect");
}

if (typeof tls.connect === "function") {
  tls.connect = () => blocked("tls.connect");
}
