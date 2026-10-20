pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

var json = pm.response.json();
if (json.page_info && json.page_info.next_cursor) {
    pm.collectionVariables.set("current_cursor", json.page_info.next_cursor);
} else {
    pm.collectionVariables.unset("current_cursor");
}