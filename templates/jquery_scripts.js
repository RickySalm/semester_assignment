$(document).ready(function() {
    $(".add_step").click(function(e) {
        e.preventDefault();
        $('.recipe_form').append('                <div>\n' +
            '                    <div>\n' +
            '                        <label>Image</label>\n' +
            '                        <input type="file" accept="image/*" name="image_step">\n' +
            '                    </div>\n' +
            '                    <div>\n' +
            '                        <label>Text</label>\n' +
            '                        <input type="text" name="text_step">\n' +
            '                    </div>\n' +
            '                </div>');
    });
});
