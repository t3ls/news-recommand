{% if theme.widget.Tags %}
    <section id="tags" class="widget-area widget_tags">
        <h3 class="widget-title">Tags</h3>
        {{ list_tags({show_count: true, amount: 20, orderby: 'count'}) }}
    </section>
{% endif %}
