const copyToClipboard = async (copyThis) => {
    try {
        await navigator.clipboard.writeText(copyThis);
    } catch (err) {
        console.error('Failed to copy: ', err);
    }
}

const copyTextContentToClipboard = (elementId) => copyToClipboard(document.getElementById(elementId).textContent)