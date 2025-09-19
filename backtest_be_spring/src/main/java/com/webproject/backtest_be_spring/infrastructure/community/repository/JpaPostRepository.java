package com.webproject.backtest_be_spring.infrastructure.community.repository;

import com.webproject.backtest_be_spring.domain.community.model.Post;
import com.webproject.backtest_be_spring.domain.community.model.PostCategory;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface JpaPostRepository extends JpaRepository<Post, Long> {

    Optional<Post> findByIdAndDeletedFalse(Long id);

    Page<Post> findByDeletedFalse(Pageable pageable);

    Page<Post> findByCategoryAndDeletedFalse(PostCategory category, Pageable pageable);

    @Query("SELECT p FROM Post p WHERE p.deleted = false AND (LOWER(p.title) LIKE LOWER(CONCAT('%', :kw, '%')) OR LOWER(p.content) LIKE LOWER(CONCAT('%', :kw, '%')))")
    Page<Post> search(@Param("kw") String keyword, Pageable pageable);

    long countByDeletedFalse();

    @Modifying
    @Query("UPDATE Post p SET p.viewCount = p.viewCount + 1 WHERE p.id = :id")
    void incrementViewCount(@Param("id") Long postId);

    @Modifying
    @Query("UPDATE Post p SET p.likeCount = p.likeCount + :delta WHERE p.id = :id")
    void adjustLikeCount(@Param("id") Long postId, @Param("delta") long delta);

    @Modifying
    @Query("UPDATE Post p SET p.commentCount = p.commentCount + :delta WHERE p.id = :id")
    void adjustCommentCount(@Param("id") Long postId, @Param("delta") long delta);
}
