on_items_added = ->
  $('.feedback-json').each( ->
    t = $(@)
    t.removeClass('feedback-json')
    f = JSON.parse(t.text())
    t.text('')

    demog_fields = ['age', 'gender', 'language', 'city', 'country']
    html = (f[k] for k in demog_fields when f[k]?).join(', ')

    if html != ''
      t.append($("<p><i>Demographics:</i></p>"))
      t.append($("<blockquote><p>#{html}</p></blockquote>"))

    if f.thoughts?
      t.append($('<p><i>What did you think of the task?</i></p>'))
      t.append($("<blockquote><p>#{f.thoughts}</p></blockquote>"))

    if f.understand?
      t.append($('<p><i>What parts didn\'t you understand?</i></p>'))
      t.append($("<blockquote><p>#{f.understand}</p></blockquote>"))

    if f.other?
      t.append($('<p><i>Any other feeedback or suggestions?</i></p>'))
      t.append($("<blockquote><p>#{f.other}</p></blockquote>"))

    t.css('display', '')
  )

$(document).on('items-added', on_items_added)
$( -> on_items_added())
