document.addEventListener("DOMContentLoaded", function() {
    const tenancyFormForNum = num => `id_tenancy_set-${num}-address`

    params = new URLSearchParams(window.location.search)
    address_id = params.get("address_id")

    if (!address_id) return
    
    counter = 0
    found = false

    while (!found) {
        el = document.getElementById(tenancyFormForNum(counter))
        if (!el) break
        el.value ? counter ++ : found = true
    }
    
    if (!found) return

    document.getElementById(tenancyFormForNum(counter)).value = address_id
});